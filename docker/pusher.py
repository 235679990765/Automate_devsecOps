import subprocess

def push_image(image: str):
    subprocess.run(["docker", "push", image], check=True)
    return {"status": "pushed", "image": image}
