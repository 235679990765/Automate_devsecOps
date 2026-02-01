# docker/env.py
from pathlib import Path

def write_env_file(service_path: Path, env: dict):
    if not env:
        return None
    p = service_path / ".env"
    with p.open("w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")
    return p
