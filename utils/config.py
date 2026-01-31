IGNORE_DIRS = {
    ".git", "node_modules", "venv", "__pycache__",
    "dist", "build", "target", ".idea", ".vscode"
}

ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".json", ".yml"}
MAX_FILE_SIZE = 1_000_000      # 1 MB
MAX_FILES_SCAN = 500
SCAN_TIMEOUT = 20               # seconds
