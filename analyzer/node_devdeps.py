import json
from pathlib import Path

IGNORE_DIRS = {
    "node_modules",
    "test", "tests", "__tests__",
    "examples", "docs",
    ".github"
}

RUNTIME_ROOT_FILES = {
    "index.js", "app.js", "server.js", "main.js"
}

DEV_RUNTIME_TOOLS = {
    "nodemon",
    "ts-node",
    "typescript",
    "babel",
    "@babel/core",
    "webpack",
    "vite",
    "react-scripts"
}


def analyze_node_dev_dependencies(service_path: Path):
    pkg_file = service_path / "package.json"
    if not pkg_file.exists():
        return None

    pkg = json.loads(pkg_file.read_text(errors="ignore"))
    dev_deps = set(pkg.get("devDependencies", {}).keys())
    scripts = pkg.get("scripts", {})

    reasons = set()
    runtime_dev_required = False

    # Rule 1: start script uses dev tool
    start_script = scripts.get("start", "")
    for tool in DEV_RUNTIME_TOOLS:
        if tool in start_script:
            runtime_dev_required = True
            reasons.add(f"start script uses {tool}")

    # Rule 2: TypeScript runtime
    if (service_path / "tsconfig.json").exists():
        runtime_dev_required = True
        reasons.add("tsconfig.json present")

    # Rule 3: Runtime imports (FILTERED)
    for file in service_path.rglob("*.js"):
        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        if file.name not in RUNTIME_ROOT_FILES and "src" not in file.parts:
            continue

        try:
            content = file.read_text(errors="ignore")
            for dep in dev_deps:
                if f"require('{dep}')" in content or f'import {dep}' in content:
                    runtime_dev_required = True
                    reasons.add(f"{dep} imported at runtime")
        except:
            continue

    return {
        "has_dev_dependencies": bool(dev_deps),
        "dev_deps_required_at_runtime": runtime_dev_required,
        "safe_production_install": not runtime_dev_required,
        "reasons": sorted(reasons)
    }
