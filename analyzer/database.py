from analyzer.scanner import iter_files

DB_SIGNATURES = {
    "postgresql": {
        "keywords": ["psycopg2", "asyncpg", "postgresql", "jdbc:postgresql"],
        "env": ["POSTGRES_URL", "DATABASE_URL"]
    },
    "mysql": {
        "keywords": ["mysql", "pymysql", "mysqldb", "jdbc:mysql"],
        "env": ["MYSQL_URL"]
    },
    "mongodb": {
        "keywords": ["mongodb", "mongoose"],
        "env": ["MONGO_URL", "MONGODB_URI"]
    },
    "redis": {
        "keywords": ["redis"],
        "env": ["REDIS_URL"]
    }
}


def detect_database(repo):
    detected = set()
    detected_from = set()
    env_vars = set()

    for file in iter_files(repo):
        try:
            content = file.read_text(errors="ignore").lower()

            for db, rules in DB_SIGNATURES.items():
                if any(k in content for k in rules["keywords"]):
                    detected.add(db)
                    detected_from.add("source")

                for env in rules["env"]:
                    if env.lower() in content:
                        detected.add(db)
                        env_vars.add(env)
                        detected_from.add("env")

        except Exception:
            continue

    return {
        "used": bool(detected),
        "types": sorted(detected),
        "detected_from": sorted(detected_from),
        "env_vars": sorted(env_vars)
    }
