from fastapi import FastAPI, Request, Body, Depends, HTTPException, status, Response, Cookie, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import threading
import time
import os
import secrets
from collector import dir_collector, cloudwatch_collector, api_collector
from processor import parser
from intelligence.analyzer import LogAnalyzer
from db import Log, SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state for logs and analysis
dashboard_logs = []
dashboard_analysis = {"counts": {}, "anomalies": []}

analyzer = LogAnalyzer(window_seconds=60)

log_source = {"type": "local", "group": None, "stream": None, "region": None, "api_url": None}
log_thread = None

SESSION_COOKIE = "session_id"
VALID_USERNAME = "admin"
VALID_PASSWORD = "password"
SESSIONS = set()

# Helper to start the correct log collector thread
def start_log_collector():
    global log_thread
    if log_thread and log_thread.is_alive():
        # No safe way to kill a thread, so just ignore and start a new one
        pass
    def collector():
        global dashboard_analysis
        dashboard_logs.clear()
        analyzer.logs.clear()
        if log_source["type"] == "local":
            for raw_log in dir_collector.tail_directory("logs"):
                parsed_log = parser.parse_log(raw_log["message"])
                parsed_log.update(raw_log)
                dashboard_logs.append(parsed_log)
                if len(dashboard_logs) > 100:
                    dashboard_logs.pop(0)
                analyzer.add_log(parsed_log)
                save_log_to_db(parsed_log)
                dashboard_analysis = analyzer.analyze()
        elif log_source["type"] == "cloudwatch":
            for raw_log in cloudwatch_collector.cloudwatch_logs(
                log_source["group"], log_source["stream"], log_source["region"] or "us-east-1"
            ):
                parsed_log = parser.parse_log(raw_log["message"])
                parsed_log.update(raw_log)
                dashboard_logs.append(parsed_log)
                if len(dashboard_logs) > 100:
                    dashboard_logs.pop(0)
                analyzer.add_log(parsed_log)
                save_log_to_db(parsed_log)
                dashboard_analysis = analyzer.analyze()
        elif log_source["type"] == "api":
            for raw_log in api_collector.fetch_logs_from_api(log_source["api_url"]):
                parsed_log = parser.parse_log(raw_log["message"])
                parsed_log.update(raw_log)
                dashboard_logs.append(parsed_log)
                if len(dashboard_logs) > 100:
                    dashboard_logs.pop(0)
                analyzer.add_log(parsed_log)
                save_log_to_db(parsed_log)
                dashboard_analysis = analyzer.analyze()
    log_thread = threading.Thread(target=collector, daemon=True)
    log_thread.start()

def get_current_user(session_id: str = Cookie(None)):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return VALID_USERNAME

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == VALID_USERNAME and form_data.password == VALID_PASSWORD:
        session_id = secrets.token_hex(16)
        SESSIONS.add(session_id)
        response = JSONResponse({"message": "Login successful"})
        response.set_cookie(key=SESSION_COOKIE, value=session_id, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
def logout(session_id: str = Cookie(None)):
    SESSIONS.discard(session_id)
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE)
    return response

# Protect dashboard and API endpoints
def require_auth(user: str = Depends(get_current_user)):
    return user

@app.get("/", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/logs", dependencies=[Depends(require_auth)])
def get_logs():
    return JSONResponse(dashboard_logs[-50:])

@app.get("/api/anomalies", dependencies=[Depends(require_auth)])
def get_anomalies():
    return JSONResponse(dashboard_analysis)

@app.post("/api/source", dependencies=[Depends(require_auth)])
def set_source(data: dict = Body(...)):
    """Set the log source. data = {type: 'local'|'cloudwatch'|'api', ...} """
    log_source.update(data)
    start_log_collector()
    return {"status": "ok", "source": log_source}

@app.get("/api/db_logs", dependencies=[Depends(require_auth)])
def get_db_logs(
    level: str = Query(None),
    user_id: str = Query(None),
    service_id: str = Query(None),
    keyword: str = Query(None),
    start_time: float = Query(None),
    end_time: float = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    db = SessionLocal()
    try:
        query = db.query(Log)
        if level:
            query = query.filter(Log.level == level)
        if user_id:
            query = query.filter(Log.user_id == user_id)
        if service_id:
            query = query.filter(Log.service_id == service_id)
        if keyword:
            query = query.filter(Log.message.contains(keyword))
        if start_time:
            query = query.filter(Log.timestamp >= start_time)
        if end_time:
            query = query.filter(Log.timestamp <= end_time)
        logs = query.order_by(Log.timestamp.desc()).limit(limit).all()
        return [
            {
                "timestamp": log.timestamp,
                "level": log.level,
                "message": log.message,
                "user_id": log.user_id,
                "service_id": log.service_id,
                "request_id": log.request_id,
                "source": log.source
            }
            for log in logs
        ]
    finally:
        db.close()

def save_log_to_db(parsed_log):
    db = SessionLocal()
    try:
        # Handle both JSON and plain text logs
        user_id = parsed_log.get('user_id')
        service_id = parsed_log.get('service_id')
        request_id = parsed_log.get('request_id')
        # Try to extract from JSON message if not present
        try:
            import json
            msg_obj = json.loads(parsed_log.get('message', ''))
            if isinstance(msg_obj, dict):
                user_id = user_id or msg_obj.get('user_id')
                service_id = service_id or msg_obj.get('service_id')
                request_id = request_id or msg_obj.get('request_id')
        except Exception:
            pass
        db_log = Log(
            timestamp=parsed_log.get('timestamp'),
            level=parsed_log.get('level'),
            message=parsed_log.get('message'),
            user_id=user_id,
            service_id=service_id,
            request_id=request_id,
            source=parsed_log.get('source')
        )
        db.add(db_log)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print(f"DB error: {e}")
    finally:
        db.close()

# Start with local logs by default
start_log_collector()
