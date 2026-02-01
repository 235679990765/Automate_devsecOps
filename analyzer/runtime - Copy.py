def detect_runtime(language):
    if language == "frontend-static":
        return {
            "start": "nginx -g 'daemon off;'",
            "port": 80
        }

    if language == "python":
        return {"start": "python main.py", "port": 8000}

    if language == "node":
        return {"start": "npm start", "port": 3000}

    if language == "java":
        return {"start": "java -jar app.jar", "port": 8080}

    return {"start": None, "port": None}
