import time
from collections import deque, Counter

class LogAnalyzer:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.logs = deque()

    def add_log(self, log):
        """Add new log and clean up old logs outside window"""
        now = time.time()
        self.logs.append(log)

        # Keep only logs within rolling window
        while self.logs and now - self.logs[0]["timestamp"] > self.window_seconds:
            self.logs.popleft()

    def analyze(self):
        levels = [log["level"] for log in self.logs]
        counts = Counter(levels)

        anomalies = []
        now = time.time()

        # Rule 1: Error spike (>=5 errors in last 10 sec)
        recent_errors = [l for l in self.logs if l["level"] == "ERROR" and now - l["timestamp"] <= 10]
        if len(recent_errors) >= 5:
            anomalies.append("Error spike detected")

        # Rule 2: Critical escalation
        if "CRITICAL" in levels:
            anomalies.append("Critical system failure detected")

        # Rule 3: Error-to-info ratio (more than 50% errors)
        total_logs = len(self.logs)
        if total_logs > 0 and counts["ERROR"] / total_logs > 0.5:
            anomalies.append("System instability: too many errors")

        return {
            "counts": dict(counts),
            "anomalies": anomalies
        }