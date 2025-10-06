import time
import os
import re
import subprocess
import platform
import threading

def parse_system_log_line(line):
    # Handle different log formats
    
    # macOS unified logging format (from `log` command):
    # 2025-09-24 15:45:30.123456+0000  localhost   kernel[0]: (AppleACPIPlatform) AppleACPIPlatform
    unified_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+[+-]\d{4})\s+([^\s]+)\s+([^:]+):\s*(.*)$'
    match = re.match(unified_pattern, line)
    if match:
        timestamp, hostname, source, message = match.groups()
        level = detect_log_level(message)
        return {
            "timestamp": timestamp,
            "hostname": hostname,
            "source": source.strip(),
            "level": level,
            "message": message.strip(),
            "log_type": "system"
        }
    
    # Traditional syslog format:
    # Sep 24 10:15:32 MacBook-Air syslogd[46]: ASL Sender Statistics
    syslog_pattern = r'^(\w{3} \d{1,2} \d{2}:\d{2}:\d{2}) ([^ ]+) ([^:]+): (.*)$'
    match = re.match(syslog_pattern, line)
    if match:
        timestamp, hostname, source, message = match.groups()
        level = detect_log_level(message)
        return {
            "timestamp": timestamp,
            "hostname": hostname,
            "source": source.strip(),
            "level": level,
            "message": message.strip(),
            "log_type": "system"
        }
    
    # Fallback for unrecognized format
    level = detect_log_level(line)
    return {
        "timestamp": None,
        "hostname": "localhost",
        "source": "system",
        "level": level,
        "message": line.strip(),
        "log_type": "system"
    }

def detect_log_level(message):
    """Detect log level from message content"""
    message_lower = message.lower()
    if any(word in message_lower for word in ["critical", "fatal", "panic", "emergency"]):
        return "CRITICAL"
    elif any(word in message_lower for word in ["error", "err", "failed", "failure", "exception"]):
        return "ERROR"
    elif any(word in message_lower for word in ["warn", "warning", "caution"]):
        return "WARNING"
    elif any(word in message_lower for word in ["debug", "trace"]):
        return "DEBUG"
    else:
        return "INFO"

def generate_mock_system_logs(callback=None, stop_event=None):
    """Generate mock system logs for demonstration purposes"""
    import random
    from datetime import datetime
    
    mock_logs = [
        "kernel[0]: (AppleACPIPlatform) AppleACPIPlatform: ACPI device power state changed",
        "com.apple.xpc.launchd[1]: Service exited with abnormal code: 1",
        "kernel[0]: IOBluetoothHCIController: Bluetooth controller detected",
        "syslogd[46]: Configuration Notice: ASL Module com.apple.cdscheduler",
        "kernel[0]: Warning: Memory pressure detected, free pages: 1024",
        "loginwindow[89]: User session started for user: admin",
        "com.apple.SecurityServer[23]: Error: Authentication failed for user",
        "kernel[0]: Critical: Disk space critically low on volume /",
        "networkd[456]: Network interface en0 status changed to active",
        "com.apple.dock[234]: Dock process restarted successfully"
    ]
    
    sources = ["kernel[0]", "syslogd[46]", "loginwindow[89]", "com.apple.SecurityServer[23]", 
               "networkd[456]", "com.apple.dock[234]", "com.apple.xpc.launchd[1]"]
    
    while not (stop_event and stop_event.is_set()):
        # Generate a random log entry
        message = random.choice(mock_logs)
        source = random.choice(sources)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f+0000")
        hostname = "localhost"
        
        log_line = f"{timestamp}  {hostname}   {source}: {message}"
        parsed = parse_system_log_line(log_line)
        
        if callback:
            callback(parsed)
        else:
            print(parsed)
        
        # Wait between 1-5 seconds before next log
        time.sleep(random.uniform(1, 5))

def tail_system_log_macos(callback=None, stop_event=None):
    """Use macOS unified logging system via `log` command"""
    try:
        # Start streaming macOS unified logs
        cmd = ["log", "stream", "--predicate", "eventType == logEvent", "--style", "compact"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 universal_newlines=True, bufsize=1)
        
        while not (stop_event and stop_event.is_set()):
            line = process.stdout.readline()
            if line:
                parsed = parse_system_log_line(line)
                if callback:
                    callback(parsed)
            else:
                time.sleep(0.1)
                
        process.terminate()
        
    except Exception as e:
        print(f"Error accessing macOS unified logs: {e}")
        print("Falling back to mock system logs for demonstration...")
        generate_mock_system_logs(callback, stop_event)

def tail_system_log_file(log_path, callback=None, stop_event=None):
    """Tail a traditional log file"""
    if not os.path.exists(log_path):
        print(f"System log file not found: {log_path}")
        return
        
    with open(log_path, "r") as f:
        f.seek(0, 2)  # Go to end of file
        while not (stop_event and stop_event.is_set()):
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            parsed = parse_system_log_line(line)
            if callback:
                callback(parsed)

def tail_system_log(log_path="/var/log/system.log", callback=None, stop_event=None):
    """
    Main system log tailing function that chooses the appropriate method
    """
    # Try different approaches based on availability and platform
    
    # 1. First try traditional log file if it exists
    if os.path.exists(log_path):
        print(f"Using traditional system log file: {log_path}")
        tail_system_log_file(log_path, callback, stop_event)
        return
    
    # 2. Try macOS unified logging if on macOS and outside Docker
    if platform.system() == "Darwin" and not os.path.exists("/.dockerenv"):
        try:
            print("Using macOS unified logging system...")
            tail_system_log_macos(callback, stop_event)
            return
        except Exception as e:
            print(f"Failed to use macOS unified logging: {e}")
    
    # 3. Fallback to mock logs for demonstration (especially useful in Docker)
    print("Using mock system logs for demonstration...")
    generate_mock_system_logs(callback, stop_event)

# Example usage: send to backend
if __name__ == "__main__":
    def print_log(log):
        print(log)
    
    # Create a stop event for clean shutdown
    import threading
    stop_event = threading.Event()
    
    try:
        tail_system_log(callback=print_log, stop_event=stop_event)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
