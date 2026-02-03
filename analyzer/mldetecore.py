def detect_ml(repo):
    frameworks = set()
    model_files = []

    for f in repo.rglob("*"):
        name = f.name.lower()

        # model files
        if name.endswith((".pkl", ".pt", ".onnx", ".h5")):
            model_files.append(str(f))

        # python ML
        if name in ["requirements.txt", "pyproject.toml"]:
            text = f.read_text(errors="ignore").lower()
            if "torch" in text:
                frameworks.add("pytorch")
            if "tensorflow" in text:
                frameworks.add("tensorflow")
            if "sklearn" in text:
                frameworks.add("sklearn")

        # node ML
        if name == "package.json":
            text = f.read_text(errors="ignore").lower()
            if "tensorflow" in text:
                frameworks.add("tensorflow-js")
            if "onnxruntime" in text:
                frameworks.add("onnx")

    if not frameworks and not model_files:
        return {"enabled": False}

    return {
        "enabled": True,
        "frameworks": list(frameworks),
        "model_files": model_files,
        "type": "inference" if model_files else "training"
    }
