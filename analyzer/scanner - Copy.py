import time
from pathlib import Path
from utils.config import *

def iter_files(repo: Path):
    start = time.time()
    count = 0

    for path in repo.rglob("*"):
        if time.time() - start > SCAN_TIMEOUT:
            break

        if any(p in IGNORE_DIRS for p in path.parts):
            continue

        if path.is_file():
            if path.suffix not in ALLOWED_EXTENSIONS:
                continue

            if path.stat().st_size > MAX_FILE_SIZE:
                continue

            yield path
            count += 1

        if count >= MAX_FILES_SCAN:
            break
