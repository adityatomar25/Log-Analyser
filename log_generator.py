import os
import time
import random

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

def write_log(file_path, message, level):
    """Write a single log entry"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} {level} {message}\n"
    with open(file_path, "a") as f:
        f.write(log_line)

def generate_logs():
    """Keep generating random logs forever"""
    while True:
        app = random.choice(APPS)
        level = random.choices(
            list(LOG_LEVELS.keys()), 
            weights=[60, 20, 15, 5]  # INFO more frequent, CRITICAL rare
        )[0]
        message = random.choice(LOG_LEVELS[level])
        file_path = os.path.join(LOG_DIR, app)

        write_log(file_path, message, level)
        print(f"📝 {app} → {level}: {message}")

        time.sleep(random.uniform(0.5, 2.0))  # wait before next log

if __name__ == "__main__":
    print("🚀 Starting automatic log generator...")
    generate_logs()