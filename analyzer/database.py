from analyzer.scanner import iter_files

DB_KEYWORDS = {
    # Python
    "sqlalchemy", "psycopg2", "asyncpg",
    # Node
    "mongoose", "sequelize", "typeorm",
    # Java
    "spring-data", "hibernate", "jdbc", "jpa"
}

def detect_database(repo):
    for file in iter_files(repo):
        content = file.read_text(errors="ignore").lower()
        if any(k in content for k in DB_KEYWORDS):
            return True
    return False
