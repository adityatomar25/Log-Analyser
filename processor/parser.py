import re
import json

# Regex patterns to detect log levels
LOG_LEVELS = {
    "ERROR": re.compile(r"error", re.IGNORECASE),
    "WARNING": re.compile(r"warn", re.IGNORECASE),
    "INFO": re.compile(r"info", re.IGNORECASE),
    "CRITICAL": re.compile(r"critical", re.IGNORECASE),
}


def categorize_log(log: dict) -> dict:
    """
    Takes a log dict (from collector) and adds a 'level' field.
    Example input: {"message": "2025-08-26 ERROR Database down"}
    Example output: {"message": "...", "level": "ERROR"}
    """
    message = log.get("message", "")

    # Try to parse JSON log message
    try:
        msg_obj = json.loads(message)
        if isinstance(msg_obj, dict) and "level" in msg_obj:
            log["level"] = msg_obj.get("level", "INFO")
            log["message"] = msg_obj.get("message", message)
            if "timestamp" in msg_obj:
                log["timestamp"] = msg_obj["timestamp"]
            return log
    except Exception:
        pass

    # Try to extract [LEVEL] from bracketed log lines
    bracket_match = re.search(r"\[(ERROR|WARNING|INFO|CRITICAL)\]", message, re.IGNORECASE)
    if bracket_match:
        log["level"] = bracket_match.group(1).upper()
        return log

    # Try to extract LEVEL from space-separated log lines (e.g. '2025-08-26 ERROR ...')
    space_match = re.search(r"\b(ERROR|WARNING|INFO|CRITICAL)\b", message, re.IGNORECASE)
    if space_match:
        log["level"] = space_match.group(1).upper()
        return log

    # Fallback to regex patterns
    for level, pattern in LOG_LEVELS.items():
        if pattern.search(message):
            log["level"] = level
            return log

    # Default to INFO if nothing matches
    log["level"] = "INFO"
    return log


def parse_log(log_message: str) -> dict:
    """
    Wrapper for main.py — accepts a raw message string and returns structured log.
    """
    return categorize_log({"message": log_message})


if __name__ == "__main__":
    # Test with dummy logs
    sample_logs = [
        "2025-08-26 INFO Server started",
        "2025-08-26 ERROR Database down",
        "2025-08-26 WARNING Disk usage high",
    ]
    for msg in sample_logs:
        print(parse_log(msg))