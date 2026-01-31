import subprocess

def docker_login(username: str, token: str):
    process = subprocess.Popen(
        ["docker", "login", "-u", username, "--password-stdin"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    _, err = process.communicate(input=token.encode())

    if process.returncode != 0:
        raise RuntimeError(f"Docker login failed: {err.decode()}")
