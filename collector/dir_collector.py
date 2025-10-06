import os
import time

def tail_directory(directory_path):
    """
    Continuously tails all .log files in a directory.
    """
    file_positions = {}

    # On startup, yield all existing lines in all log files
    for filename in os.listdir(directory_path):
        if not filename.endswith(".log"):
            continue
        file_path = os.path.join(directory_path, filename)
        with open(file_path, "r") as f:
            for line in f:
                yield {
                    "timestamp": time.time(),
                    "source": file_path,
                    "message": line.strip(),
                }
        file_positions[file_path] = os.path.getsize(file_path)

    # Now tail new lines as before
    while True:
        for filename in os.listdir(directory_path):
            if not filename.endswith(".log"):
                continue
            file_path = os.path.join(directory_path, filename)
            if file_path not in file_positions:
                file_positions[file_path] = 0
            with open(file_path, "r") as f:
                f.seek(file_positions[file_path])
                new_lines = f.readlines()
                file_positions[file_path] = f.tell()
            for line in new_lines:
                yield {
                    "timestamp": time.time(),
                    "source": file_path,
                    "message": line.strip(),
                }
        time.sleep(1)