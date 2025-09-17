import os
import time
import random
import json
import shutil

# Directory where logs will be written
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Fake applications
APPS = ["app1.log", "app2.log", "db.log"]

# Different log levels and messages
LOG_LEVELS = {
    "INFO": [
        "Started successfully",
        "Background job running",
        "User login successful",
        "Service heartbeat OK",
        "Booting up"
    ],
    "WARNING": [
        "High memory usage",
        "Disk space low",
        "Slow response time",
        "Thread pool saturation"
    ],
    "ERROR": [
        "Timeout",
        "Crash detected",
        "Database connection failed",
        "Cache miss",
        "Request timeout",
        "Disk read failed"
    ],
    "CRITICAL": [
        "Kernel panic",
        "Data corruption detected",
        "Fatal memory leak",
        "System halt required"
    ]
}

USER_IDS = [f"user{n}" for n in range(1, 11)]
SERVICE_IDS = ["svc-auth", "svc-db", "svc-api", "svc-cache"]

LOG_ROTATE_SIZE = 1 * 1024 * 1024  # 1MB


def rotate_log(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > LOG_ROTATE_SIZE:
        base, ext = os.path.splitext(file_path)
        rotated = f"{base}_{int(time.time())}{ext}"
        shutil.move(file_path, rotated)


def write_log(file_path, message, level, as_json, timestamp, user_id, service_id, request_id):
    rotate_log(file_path)
    if as_json:
        log_obj = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "user_id": user_id,
            "service_id": service_id,
            "request_id": request_id
        }
        log_line = json.dumps(log_obj) + "\n"
    else:
        log_line = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))} {level} [{user_id}] [{service_id}] [{request_id}] {message}\n"
    with open(file_path, "a") as f:
        f.write(log_line)


def generate_logs():
    burst_mode = False
    burst_count = 0
    while True:
        app = random.choice(APPS)
        # Burst mode: simulate error spike
        if burst_mode:
            level = random.choices(["ERROR", "CRITICAL"], weights=[80, 20])[0]
            burst_count -= 1
            if burst_count <= 0:
                burst_mode = False
        else:
            level = random.choices(
                list(LOG_LEVELS.keys()),
                weights=[60, 20, 15, 5]
            )[0]
            # Occasionally start a burst
            if level in ["ERROR", "CRITICAL"] and random.random() < 0.2:
                burst_mode = True
                burst_count = random.randint(3, 8)
        message = random.choice(LOG_LEVELS[level])
        file_path = os.path.join(LOG_DIR, app)
        as_json = random.random() < 0.5
        # Simulate variable timestamps (some logs in the past 0-120 seconds)
        timestamp = time.time() - random.randint(0, 120)
        user_id = random.choice(USER_IDS)
        service_id = random.choice(SERVICE_IDS)
        request_id = f"req-{random.randint(1000,9999)}"
        write_log(file_path, message, level, as_json, timestamp, user_id, service_id, request_id)
        print(f"📝 {app} → {level}: {message} ({'JSON' if as_json else 'PLAIN'})")
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    print("🚀 Starting automatic log generator...")
    generate_logs()