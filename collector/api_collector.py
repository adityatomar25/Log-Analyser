import requests
import time

def fetch_logs_from_api(api_url, poll_interval=2):
    """
    Continuously fetch logs from a REST API endpoint that returns a list of log entries.
    Each log entry should be a dict with at least a 'message' field.
    """
    last_id = None
    while True:
        params = {"after_id": last_id} if last_id else {}
        try:
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            logs = response.json()  # Expecting a list of dicts
            for log in logs:
                last_id = log.get("id", last_id)
                yield {
                    "timestamp": log.get("timestamp", time.time()),
                    "source": api_url,
                    "message": log.get("message", "")
                }
        except Exception as e:
            print(f"API fetch error: {e}")
        time.sleep(poll_interval)
