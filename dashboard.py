import os
import yaml
import json
import hashlib

def get_env_or_config(key, default=None):
    return os.environ.get(key.upper(), config.get(key, default))

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

GMAIL_USER = get_env_or_config("gmail_user")
GMAIL_APP_PASSWORD = get_env_or_config("gmail_app_password")
ALERT_RECIPIENT = get_env_or_config("alert_recipient")
SLACK_WEBHOOK_URL = get_env_or_config("slack_webhook_url")

import requests
ALERT_STATE_FILE = "alert_state.json"
ALERTS_PAUSED_FILE = "alerts_paused.flag"

def get_alert_state():
    try:
        with open(ALERT_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"last_alert": 0, "last_hash": None}

def set_alert_state(ts, msg_hash):
    try:
        with open(ALERT_STATE_FILE, "w") as f:
            json.dump({"last_alert": ts, "last_hash": msg_hash}, f)
    except Exception as e:
        print(f"[AlertState] Failed to write: {e}")

def are_alerts_paused():
    import os
    return os.path.exists(ALERTS_PAUSED_FILE)

def set_alerts_paused(paused: bool):
    import os
    if paused:
        with open(ALERTS_PAUSED_FILE, "w") as f:
            f.write("paused")
    else:
        if os.path.exists(ALERTS_PAUSED_FILE):
            os.remove(ALERTS_PAUSED_FILE)

def send_slack_alert(message):
    if are_alerts_paused():
        print("[Slack] Alerts are paused. Not sending alert.")
        return
    import time
    RATE_LIMIT_SECONDS = 300  # 5 minutes
    now = time.time()
    state = get_alert_state()
    msg_hash = hashlib.sha256(message.encode()).hexdigest()
    if now - state.get("last_alert", 0) < RATE_LIMIT_SECONDS and state.get("last_hash") == msg_hash:
        print("[Alert] Duplicate or rate-limited Slack alert not sent.")
        return
    if not SLACK_WEBHOOK_URL:
        print("[Slack] Webhook URL not configured. Alert not sent.")
        return
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"[Slack] Failed to send alert: {response.text}")
        set_alert_state(now, msg_hash)
    except Exception as e:
        print(f"[Slack] Exception: {e}")

import smtplib
from email.mime.text import MIMEText

def send_email_alert(subject, body):
    import time
    RATE_LIMIT_SECONDS = 300  # 5 minutes
    now = time.time()
    state = get_alert_state()
    msg_hash = hashlib.sha256(body.encode()).hexdigest()
    if now - state.get("last_alert", 0) < RATE_LIMIT_SECONDS and state.get("last_hash") == msg_hash:
        print("[Alert] Duplicate or rate-limited email not sent.")
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = ALERT_RECIPIENT
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, [ALERT_RECIPIENT], msg.as_string())
        set_alert_state(now, msg_hash)
    except Exception as e:
        print(f"[Email] Exception: {e}")

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
# User store with roles
USERS = {
    "admin": {"password": "password", "role": "admin"},
    "user": {"password": "userpass", "role": "user"}
}
SESSIONS = {}  # session_id -> username

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
                # --- ALERTING LOGIC START ---
                error_count = dashboard_analysis['counts'].get('ERROR', 0)
                critical_count = dashboard_analysis['counts'].get('CRITICAL', 0)
                if error_count + critical_count > 5:
                    alert_msg = f"More than 5 ERROR/CRITICAL logs detected in the last 60 seconds.\nCounts: ERROR={error_count}, CRITICAL={critical_count}"
                    # send_email_alert(
                    #     subject="Log Anomaly Detected!",
                    #     body=alert_msg
                    # )
                    send_slack_alert(alert_msg)
                # --- ALERTING LOGIC END ---
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
                # --- ALERTING LOGIC START ---
                error_count = dashboard_analysis['counts'].get('ERROR', 0)
                critical_count = dashboard_analysis['counts'].get('CRITICAL', 0)
                if error_count + critical_count > 5:
                    send_email_alert(
                        subject="Log Anomaly Detected!",
                        body=f"More than 5 ERROR/CRITICAL logs detected in the last 60 seconds.\n\nCounts: ERROR={error_count}, CRITICAL={critical_count}"
                    )
                # --- ALERTING LOGIC END ---
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
                # --- ALERTING LOGIC START ---
                error_count = dashboard_analysis['counts'].get('ERROR', 0)
                critical_count = dashboard_analysis['counts'].get('CRITICAL', 0)
                if error_count + critical_count > 5:
                    send_email_alert(
                        subject="Log Anomaly Detected!",
                        body=f"More than 5 ERROR/CRITICAL logs detected in the last 60 seconds.\n\nCounts: ERROR={error_count}, CRITICAL={critical_count}"
                    )
                # --- ALERTING LOGIC END ---
    log_thread = threading.Thread(target=collector, daemon=True)
    log_thread.start()

def get_current_user(session_id: str = Cookie(None)):
    username = SESSIONS.get(session_id)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

def get_current_role(session_id: str = Cookie(None)):
    username = SESSIONS.get(session_id)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return USERS[username]["role"]

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form_data.username)
    if user and form_data.password == user["password"]:
        session_id = secrets.token_hex(16)
        SESSIONS[session_id] = form_data.username
        response = JSONResponse({"message": "Login successful", "role": user["role"]})
        response.set_cookie(key=SESSION_COOKIE, value=session_id, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
def logout(session_id: str = Cookie(None)):
    SESSIONS.pop(session_id, None)
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE)
    return response

# Decorator for role-based access
from fastapi import Security
from functools import wraps

def require_role(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, session_id: str = Cookie(None), **kwargs):
            username = SESSIONS.get(session_id)
            if not username or USERS[username]["role"] != role:
                raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
            return func(*args, session_id=session_id, **kwargs)
        return wrapper
    return decorator

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

@app.delete("/logs/{log_id}")
@require_role("admin")
def delete_log(log_id: int, session_id: str = Cookie(None)):
    db = SessionLocal()
    try:
        log_entry = db.query(Log).filter(Log.id == log_id).first()
        if not log_entry:
            raise HTTPException(status_code=404, detail="Log not found")
        db.delete(log_entry)
        db.commit()
        return {"message": "Log deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

from fastapi import APIRouter

@app.get("/alerts/paused")
def get_alerts_paused():
    return {"paused": are_alerts_paused()}

@app.post("/alerts/pause")
def set_alerts_paused_api(data: dict = Body(...)):
    paused = data.get("paused", False)
    set_alerts_paused(paused)
    return {"paused": are_alerts_paused()}

# Start with local logs by default
start_log_collector()
