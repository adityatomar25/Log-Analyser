import time, json

def tail_file(filepath):
    """
    Continuously read new lines from a log file and yield them as JSON.
    """
    with open(filepath, "r") as f:
        f.seek(0, 2)  # go to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            yield {
                "timestamp": time.time(),
                "source": filepath,
                "message": line.strip()
            }

if __name__ == "__main__":
    # test with a sample file
    for log in tail_file("test.log"):
        print(json.dumps(log, indent=2))