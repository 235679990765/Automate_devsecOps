import json

def detect_build(repo, language):
    if language == "node" and (repo / "package.json").exists():
        pkg = json.load(open(repo / "package.json"))
        return "build" in pkg.get("scripts", {})
    if language == "java":
        return True
    return False
