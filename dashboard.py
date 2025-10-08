# ...existing code...
import os
import yaml
import json
import hashlib
import time
from typing import List, Optional
from datetime import datetime

def get_env_or_config(key, default=None):
    return os.environ.get(key.upper(), config.get(key, default))


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
print(f"[DEBUG] Loaded log_source from config.yaml: {config.get('log_source')}")

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
from collector import dir_collector, cloudwatch_collector, api_collector, system_collector
from processor import parser
from intelligence.analyzer import LogAnalyzer
from db import Log, SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS to allow requests from the React frontend with Safari-specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)



# Shared state for logs and analysis
dashboard_logs = []
dashboard_analysis = {"counts": {}, "anomalies": []}
# State for API source warnings
api_source_warning = ""
# System log collection state
system_log_enabled = False
system_log_thread = None

# Initialize analyzer with Bedrock configuration
bedrock_config = config.get("bedrock", {})
analyzer = LogAnalyzer(
    window_seconds=60,
    enable_bedrock=bedrock_config.get("enabled", False),
    aws_region=bedrock_config.get("region", "ap-south-1")
)

log_source = config.get("log_source", {"type": "local", "group": None, "stream": None, "region": None, "api_url": None})
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
    print(f"[DEBUG] Starting log collector with log_source: {log_source}")
    if log_thread and log_thread.is_alive():
        print("[DEBUG] Log collector thread already running.")
        return
    def collector():
        global dashboard_analysis
        dashboard_logs.clear()
        analyzer.logs.clear()
        if log_source["type"] == "local":
            print("[DEBUG] Local log collector started.")
            # One-time batch load of all existing log lines
            import os
            for filename in os.listdir("logs"):
                if not filename.endswith(".log"):
                    continue
                file_path = os.path.join("logs", filename)
                with open(file_path, "r") as f:
                    for line in f:
                        raw_log = {
                            "timestamp": time.time(),
                            "source": file_path,
                            "message": line.strip(),
                        }
                        parsed_log = parser.parse_log(raw_log["message"])
                        parsed_log.update(raw_log)
                        dashboard_logs.append(parsed_log)
                        if len(dashboard_logs) > 100:
                            dashboard_logs.pop(0)
                        analyzer.add_log(parsed_log)
                        save_log_to_db(parsed_log)
            dashboard_analysis = analyzer.analyze()
            print(f"[DEBUG] Initial dashboard_analysis: {dashboard_analysis}")
            # Now tail new lines as before
            for raw_log in dir_collector.tail_directory("logs"):
                print(f"[DEBUG] Processing log: {raw_log}")
                parsed_log = parser.parse_log(raw_log["message"])
                parsed_log.update(raw_log)
                dashboard_logs.append(parsed_log)
                if len(dashboard_logs) > 100:
                    dashboard_logs.pop(0)
                analyzer.add_log(parsed_log)
                save_log_to_db(parsed_log)
                dashboard_analysis = analyzer.analyze()
                print(f"[DEBUG] Updated dashboard_analysis: {dashboard_analysis}")
                # --- ALERTING LOGIC START ---
                error_count = dashboard_analysis['counts'].get('ERROR', 0)
                critical_count = dashboard_analysis['counts'].get('CRITICAL', 0)
                if error_count + critical_count > 5:
                    alert_msg = f"More than 5 ERROR/CRITICAL logs detected in the last 60 seconds.\nCounts: ERROR={error_count}, CRITICAL={critical_count}"
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
            print(f"[DEBUG] Fetching logs from API: {log_source['api_url']}")
            global api_source_warning
            empty_count = 0
            for raw_log in api_collector.fetch_logs_from_api(log_source["api_url"]):
                if raw_log is None or raw_log.get("message", "") == "":
                    empty_count += 1
                    if empty_count >= 5:
                        warning_msg = "API source has returned no logs for 5 consecutive polls. Check API availability or configuration."
                        print(f"[WARNING] {warning_msg}")
                        api_source_warning = warning_msg
                        empty_count = 0
                    continue
                else:
                    empty_count = 0
                    api_source_warning = ""
                print(f"[DEBUG] Raw log from API: {raw_log}")
                parsed_log = parser.parse_log(raw_log["message"])
                print(f"[DEBUG] Parsed log: {parsed_log}")
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
                # --- ALERTING LOGIC END ---
    
    log_thread = threading.Thread(target=collector, daemon=True)
    log_thread.start()
    print("[DEBUG] Log collector thread started.")

# System log collection state
system_log_stop_event = None

def start_system_log_collector():
    global system_log_thread, system_log_enabled, system_log_stop_event
    if not system_log_enabled:
        return
    if system_log_thread and system_log_thread.is_alive():
        print("[DEBUG] System log collector thread already running.")
        return
    
    # Create a stop event for graceful shutdown
    system_log_stop_event = threading.Event()
    
    def system_log_callback(parsed_log):
        global dashboard_analysis
        # Add timestamp conversion for system logs
        if parsed_log.get('timestamp') and isinstance(parsed_log['timestamp'], str):
            parsed_log['timestamp'] = time.time()  # Use current time for now
        
        # Add to dashboard logs
        dashboard_logs.append(parsed_log)
        if len(dashboard_logs) > 100:
            dashboard_logs.pop(0)
        
        # Add to analyzer
        analyzer.add_log(parsed_log)
        save_log_to_db(parsed_log)
        
        # Update analysis
        dashboard_analysis = analyzer.analyze()
        
        # Alert on system errors
        error_count = dashboard_analysis['counts'].get('ERROR', 0)
        critical_count = dashboard_analysis['counts'].get('CRITICAL', 0)
        if error_count + critical_count > 5:
            alert_msg = f"System log anomaly: More than 5 ERROR/CRITICAL logs detected.\nCounts: ERROR={error_count}, CRITICAL={critical_count}"
            send_slack_alert(alert_msg)
    
    def system_log_worker():
        try:
            system_collector.tail_system_log(callback=system_log_callback, stop_event=system_log_stop_event)
        except Exception as e:
            print(f"[ERROR] System log collector error: {e}")
    
    system_log_thread = threading.Thread(target=system_log_worker, daemon=True)
    system_log_thread.start()
    print("[DEBUG] System log collector thread started.")

def stop_system_log_collector():
    global system_log_thread, system_log_enabled, system_log_stop_event
    system_log_enabled = False
    if system_log_stop_event:
        system_log_stop_event.set()
    if system_log_thread:
        print("[DEBUG] System log collector stopped.")

# Endpoint to get API source warning
@app.get("/api/source_warning")
def get_api_source_warning():
    return {"warning": api_source_warning}

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
        response.set_cookie(
            key=SESSION_COOKIE, 
            value=session_id, 
            httponly=True, 
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        return response
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
def logout(session_id: str = Cookie(None)):
    SESSIONS.pop(session_id, None)
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(
        key=SESSION_COOKIE, 
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    return response

@app.get("/api/auth/status")
def auth_status():
    """Check authentication status - always returns authenticated since auth is disabled"""
    return {
        "authenticated": True,
        "user": "anonymous",
        "role": "admin"
    }

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

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/logs")
def get_logs():
    return JSONResponse(dashboard_logs[-50:])

@app.get("/api/anomalies")
def get_anomalies():
    return JSONResponse(dashboard_analysis)

@app.get("/api/source")
def get_source():
    """Get the current log source configuration"""
    return log_source

@app.post("/api/source")
def set_source(data: dict = Body(...)):
    """Set the log source. data = {type: 'local'|'cloudwatch'|'api', ...} """
    log_source.update(data)
    start_log_collector()
    return {"status": "ok", "source": log_source}

@app.get("/api/db_logs")
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

# System log collection endpoints
@app.get("/api/system_logs/status")
def get_system_log_status():
    return {
        "enabled": system_log_enabled,
        "running": system_log_thread and system_log_thread.is_alive() if system_log_thread else False
    }

@app.post("/api/system_logs/toggle")
def toggle_system_logs(data: dict = Body(...)):
    global system_log_enabled
    enabled = data.get("enabled", False)
    system_log_enabled = enabled
    
    if enabled:
        start_system_log_collector()
        message = "System log collection started"
    else:
        stop_system_log_collector()
        message = "System log collection stopped"
    
    return {
        "enabled": system_log_enabled,
        "running": system_log_thread and system_log_thread.is_alive() if system_log_thread else False,
        "message": message
    }

# New Bedrock API endpoints
@app.get("/api/bedrock/status")
def get_bedrock_status():
    """Get Bedrock integration status"""
    return {
        "enabled": analyzer.enable_bedrock,
        "available": analyzer.bedrock_client is not None,
        "region": bedrock_config.get("region", "ap-south-1"),
        "models": bedrock_config.get("models", {}),
        "last_analysis": getattr(analyzer, 'last_bedrock_analysis', 0)
    }

@app.get("/api/bedrock/insights")
def get_bedrock_insights():
    """Get detailed AI insights from Bedrock analysis"""
    try:
        insights = analyzer.get_detailed_insights()
        return insights
    except Exception as e:
        return {"error": f"Failed to get insights: {str(e)}"}

@app.post("/api/bedrock/toggle")
def toggle_bedrock_analysis(data: dict = Body(...)):
    """Toggle Bedrock analysis on/off"""
    global analyzer
    
    enabled = data.get("enabled", False)
    
    try:
        if enabled and not analyzer.enable_bedrock:
            # Re-initialize with Bedrock enabled
            analyzer = LogAnalyzer(
                window_seconds=60,
                enable_bedrock=True,
                aws_region=bedrock_config.get("region", "us-east-1")
            )
            message = "Bedrock analysis enabled"
        elif not enabled and analyzer.enable_bedrock:
            # Disable Bedrock
            analyzer.enable_bedrock = False
            analyzer.bedrock_client = None
            message = "Bedrock analysis disabled"
        else:
            message = f"Bedrock analysis already {'enabled' if enabled else 'disabled'}"
        
        return {
            "enabled": analyzer.enable_bedrock,
            "available": analyzer.bedrock_client is not None,
            "message": message
        }
        
    except Exception as e:
        return {
            "enabled": False,
            "available": False,
            "message": f"Error: {str(e)}"
        }

@app.get("/api/bedrock/predictions")
def get_ai_predictions():
    """Get AI predictions about potential system issues"""
    if not analyzer.enable_bedrock or not analyzer.bedrock_client:
        return {"error": "Bedrock not available"}
    
    try:
        logs_list = list(analyzer.logs)
        predictions = analyzer.bedrock_client.predict_system_issues(logs_list)
        return predictions
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}

# Start with local logs by default
start_log_collector()

@app.get("/api/debug_logs")
def get_debug_logs():
    return {
        "log_count": len(dashboard_logs),
        "sample_logs": dashboard_logs[-10:],
        "analysis": dashboard_analysis
    }

# ==========================================
# ENHANCED AI PATTERNS & TRENDS API ENDPOINTS
# ==========================================

@app.get("/api/ai/patterns")
def get_ai_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    limit: Optional[int] = Query(50, description="Maximum number of patterns to return"),
    format: Optional[str] = Query("json", description="Response format: json, csv")
):
    """Get detailed AI pattern analysis with filtering options"""
    try:
        insights = analyzer.get_detailed_insights()
        
        if "error" in insights:
            return {"error": insights["error"], "patterns": []}
        
        classification = insights.get("classification", {})
        patterns = classification.get("patterns", [])
        
        # Apply filters
        filtered_patterns = []
        for pattern in patterns:
            # Filter by type
            if pattern_type and pattern.get("type", "").lower() != pattern_type.lower():
                continue
            
            # Filter by severity
            if severity and pattern.get("severity", "").lower() != severity.lower():
                continue
            
            # Enhance pattern with metadata
            enhanced_pattern = {
                **pattern,
                "timestamp": time.time(),
                "analyzed_logs": insights.get("total_logs_analyzed", 0),
                "confidence_score": pattern.get("confidence", 0),
                "impact_level": _calculate_impact_level(pattern),
                "actionable_insights": _generate_actionable_insights(pattern)
            }
            filtered_patterns.append(enhanced_pattern)
        
        # Apply limit
        filtered_patterns = filtered_patterns[:limit]
        
        # Format response
        if format.lower() == "csv":
            return _format_patterns_as_csv(filtered_patterns)
        
        return {
            "patterns": filtered_patterns,
            "metadata": {
                "total_found": len(filtered_patterns),
                "analysis_timestamp": time.time(),
                "bedrock_enabled": analyzer.enable_bedrock,
                "filters_applied": {
                    "pattern_type": pattern_type,
                    "severity": severity,
                    "limit": limit
                }
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get patterns: {str(e)}", "patterns": []}

@app.get("/api/ai/trends")
def get_ai_trends(
    trend_type: Optional[str] = Query(None, description="Filter by trend type"),
    timeframe: Optional[str] = Query("1h", description="Timeframe: 15m, 1h, 6h, 24h"),
    format: Optional[str] = Query("json", description="Response format: json, csv")
):
    """Get detailed AI trend analysis and forecasting"""
    try:
        insights = analyzer.get_detailed_insights()
        
        if "error" in insights:
            return {"error": insights["error"], "trends": []}
        
        classification = insights.get("classification", {})
        trends = classification.get("trends", [])
        
        # Enhance trends with time-series data
        enhanced_trends = []
        for trend in trends:
            enhanced_trend = {
                **trend,
                "timestamp": time.time(),
                "timeframe": timeframe,
                "trend_direction": _calculate_trend_direction(trend),
                "forecast": _generate_trend_forecast(trend, timeframe),
                "statistical_significance": _calculate_significance(trend),
                "recommended_actions": _generate_trend_recommendations(trend)
            }
            
            # Filter by type if specified
            if not trend_type or trend.get("type", "").lower() == trend_type.lower():
                enhanced_trends.append(enhanced_trend)
        
        # Format response
        if format.lower() == "csv":
            return _format_trends_as_csv(enhanced_trends)
        
        return {
            "trends": enhanced_trends,
            "analysis_summary": {
                "total_trends": len(enhanced_trends),
                "timeframe": timeframe,
                "analysis_timestamp": time.time(),
                "trend_categories": list(set(t.get("type", "unknown") for t in enhanced_trends))
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to get trends: {str(e)}", "trends": []}

@app.get("/api/ai/analytics/summary")
def get_analytics_summary():
    """Get comprehensive AI analytics summary with key metrics"""
    try:
        insights = analyzer.get_detailed_insights()
        
        if "error" in insights:
            return {"error": insights["error"]}
        
        classification = insights.get("classification", {})
        patterns = classification.get("patterns", [])
        trends = classification.get("trends", [])
        
        # Calculate key metrics
        pattern_stats = _calculate_pattern_statistics(patterns)
        trend_stats = _calculate_trend_statistics(trends)
        risk_assessment = _generate_risk_assessment(patterns, trends)
        
        return {
            "summary": {
                "total_patterns_detected": len(patterns),
                "total_trends_identified": len(trends),
                "logs_analyzed": insights.get("total_logs_analyzed", 0),
                "analysis_timestamp": time.time(),
                "bedrock_status": "enabled" if analyzer.enable_bedrock else "disabled"
            },
            "pattern_analytics": pattern_stats,
            "trend_analytics": trend_stats,
            "risk_assessment": risk_assessment,
            "recommendations": _generate_system_recommendations(patterns, trends)
        }
        
    except Exception as e:
        return {"error": f"Failed to generate analytics summary: {str(e)}"}

@app.post("/api/ai/export")
def export_ai_analysis(data: dict = Body(...)):
    """Export AI analysis in various formats (JSON, CSV, PDF report)"""
    try:
        export_format = data.get("format", "json").lower()
        include_patterns = data.get("include_patterns", True)
        include_trends = data.get("include_trends", True)
        include_raw_data = data.get("include_raw_data", False)
        
        insights = analyzer.get_detailed_insights()
        
        if "error" in insights:
            return {"error": insights["error"]}
        
        export_data = {
            "export_metadata": {
                "generated_at": datetime.now().isoformat(),
                "format": export_format,
                "bedrock_enabled": analyzer.enable_bedrock,
                "total_logs_analyzed": insights.get("total_logs_analyzed", 0)
            }
        }
        
        classification = insights.get("classification", {})
        
        if include_patterns:
            export_data["patterns"] = classification.get("patterns", [])
        
        if include_trends:
            export_data["trends"] = classification.get("trends", [])
        
        if include_raw_data:
            export_data["raw_insights"] = insights
        
        # Format based on requested format
        if export_format == "csv":
            return _generate_csv_export(export_data)
        elif export_format == "pdf":
            return _generate_pdf_report(export_data)
        else:  # Default to JSON
            return export_data
        
    except Exception as e:
        return {"error": f"Export failed: {str(e)}"}

# ==========================================
# HELPER FUNCTIONS FOR AI ANALYTICS
# ==========================================

def _calculate_impact_level(pattern: dict) -> str:
    """Calculate impact level based on pattern characteristics"""
    confidence = pattern.get("confidence", 0)
    severity = pattern.get("severity", "low").lower()
    
    if severity in ["critical", "high"] and confidence > 80:
        return "high"
    elif severity in ["medium", "high"] and confidence > 60:
        return "medium"
    else:
        return "low"

def _generate_actionable_insights(pattern: dict) -> List[str]:
    """Generate actionable insights for a pattern"""
    insights = []
    pattern_type = pattern.get("type", "").lower()
    
    if "error" in pattern_type or "failure" in pattern_type:
        insights.append("Review error handling and implement retry mechanisms")
        insights.append("Monitor affected services for cascading failures")
    
    if "performance" in pattern_type or "slow" in pattern_type:
        insights.append("Analyze resource utilization and optimize bottlenecks")
        insights.append("Consider scaling affected services")
    
    if "security" in pattern_type or "unauthorized" in pattern_type:
        insights.append("Review access controls and authentication mechanisms")
        insights.append("Implement additional monitoring for security events")
    
    return insights or ["Monitor pattern evolution and frequency"]

def _calculate_trend_direction(trend: dict) -> str:
    """Calculate trend direction (increasing, decreasing, stable)"""
    # This would analyze historical data points
    # For now, using placeholder logic
    count = trend.get("count", 0)
    if count > 5:
        return "increasing"
    elif count < 2:
        return "decreasing"
    else:
        return "stable"

def _generate_trend_forecast(trend: dict, timeframe: str) -> dict:
    """Generate forecast for trend based on historical data"""
    current_count = trend.get("count", 0)
    
    # Simple forecast logic (would be more sophisticated in production)
    multiplier = {"15m": 1.2, "1h": 1.5, "6h": 2.0, "24h": 3.0}.get(timeframe, 1.0)
    
    return {
        "predicted_count": int(current_count * multiplier),
        "confidence": "medium",
        "timeframe": timeframe,
        "methodology": "trend_extrapolation"
    }

def _calculate_significance(trend: dict) -> str:
    """Calculate statistical significance of trend"""
    count = trend.get("count", 0)
    
    if count >= 10:
        return "high"
    elif count >= 5:
        return "medium"
    else:
        return "low"

def _generate_trend_recommendations(trend: dict) -> List[str]:
    """Generate recommendations based on trend analysis"""
    recommendations = []
    trend_type = trend.get("type", "").lower()
    count = trend.get("count", 0)
    
    if count >= 5:
        recommendations.append(f"Investigate root cause of recurring {trend_type} pattern")
        recommendations.append("Consider implementing automated alerting for this pattern")
    
    recommendations.append("Continue monitoring for pattern evolution")
    return recommendations

def _calculate_pattern_statistics(patterns: List[dict]) -> dict:
    """Calculate comprehensive pattern statistics"""
    if not patterns:
        return {"total": 0, "by_severity": {}, "by_type": {}}
    
    severity_counts = {}
    type_counts = {}
    
    for pattern in patterns:
        severity = pattern.get("severity", "unknown")
        pattern_type = pattern.get("type", "unknown")
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
    
    return {
        "total": len(patterns),
        "by_severity": severity_counts,
        "by_type": type_counts,
        "average_confidence": sum(p.get("confidence", 0) for p in patterns) / len(patterns)
    }

def _calculate_trend_statistics(trends: List[dict]) -> dict:
    """Calculate comprehensive trend statistics"""
    if not trends:
        return {"total": 0, "by_type": {}, "total_occurrences": 0}
    
    type_counts = {}
    total_occurrences = 0
    
    for trend in trends:
        trend_type = trend.get("type", "unknown")
        count = trend.get("count", 0)
        
        type_counts[trend_type] = type_counts.get(trend_type, 0) + 1
        total_occurrences += count
    
    return {
        "total": len(trends),
        "by_type": type_counts,
        "total_occurrences": total_occurrences,
        "average_occurrences": total_occurrences / len(trends) if trends else 0
    }

def _generate_risk_assessment(patterns: List[dict], trends: List[dict]) -> dict:
    """Generate overall risk assessment"""
    high_risk_patterns = sum(1 for p in patterns if p.get("severity", "").lower() in ["high", "critical"])
    increasing_trends = sum(1 for t in trends if t.get("count", 0) >= 5)
    
    risk_score = (high_risk_patterns * 30) + (increasing_trends * 20)
    
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return {
        "risk_level": risk_level,
        "risk_score": min(risk_score, 100),
        "factors": {
            "high_risk_patterns": high_risk_patterns,
            "increasing_trends": increasing_trends,
            "total_patterns": len(patterns),
            "total_trends": len(trends)
        }
    }

def _generate_system_recommendations(patterns: List[dict], trends: List[dict]) -> List[str]:
    """Generate system-wide recommendations"""
    recommendations = []
    
    high_risk_count = sum(1 for p in patterns if p.get("severity", "").lower() in ["high", "critical"])
    if high_risk_count > 0:
        recommendations.append("Immediate attention required for high-severity patterns")
    
    frequent_trends = sum(1 for t in trends if t.get("count", 0) >= 5)
    if frequent_trends > 0:
        recommendations.append("Investigate recurring trends for root cause analysis")
    
    if not recommendations:
        recommendations.append("System appears stable - continue monitoring")
    
    return recommendations

def _format_patterns_as_csv(patterns: List[dict]) -> str:
    """Format patterns as CSV string"""
    import io
    import csv
    
    output = io.StringIO()
    if not patterns:
        return "No patterns found"
    
    writer = csv.DictWriter(output, fieldnames=patterns[0].keys())
    writer.writeheader()
    writer.writerows(patterns)
    
    return output.getvalue()

def _format_trends_as_csv(trends: List[dict]) -> str:
    """Format trends as CSV string"""
    import io
    import csv
    
    output = io.StringIO()
    if not trends:
        return "No trends found"
    
    writer = csv.DictWriter(output, fieldnames=trends[0].keys())
    writer.writeheader()
    writer.writerows(trends)
    
    return output.getvalue()

def _generate_csv_export(export_data: dict) -> dict:
    """Generate CSV export package"""
    csv_files = {}
    
    if "patterns" in export_data:
        csv_files["patterns.csv"] = _format_patterns_as_csv(export_data["patterns"])
    
    if "trends" in export_data:
        csv_files["trends.csv"] = _format_trends_as_csv(export_data["trends"])
    
    return {
        "format": "csv",
        "files": csv_files,
        "metadata": export_data.get("export_metadata", {})
    }

def _generate_pdf_report(export_data: dict) -> dict:
    """Generate PDF report (placeholder - would integrate with PDF library)"""
    return {
        "format": "pdf",
        "message": "PDF generation requires additional libraries (reportlab/weasyprint)",
        "data": export_data,
        "recommendation": "Use JSON or CSV format for now"
    }
