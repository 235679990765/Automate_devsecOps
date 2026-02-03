from pathlib import Path

def write_env_file(service_path: Path, env: dict):
    if not env:
        return None

    env_file = service_path / ".env"
    with env_file.open("w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")

    return env_file
