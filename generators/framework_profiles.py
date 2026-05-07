FRAMEWORK_PROFILES = {

    # ---------------- NODE ----------------

    "next": {
        "build": "npm run build",
        "test": "npm test || true",
        "start": "npm start"
    },

    "react": {
        "build": "npm run build",
        "test": "npm test || true",
        "start": "nginx"
    },

    "vite": {
        "build": "npm run build",
        "test": "npm test || true",
        "start": "nginx"
    },

    "express": {
        "build": None,
        "test": "npm test || true",
        "start": "node"
    },

    "nestjs": {
        "build": "npm run build",
        "test": "npm test || true",
        "start": "npm run start:prod"
    },

    # ---------------- PYTHON ----------------

    "fastapi": {
        "build": None,
        "test": "pytest || true",
        "start": "uvicorn"
    },

    "flask": {
        "build": None,
        "test": "pytest || true",
        "start": "gunicorn"
    },

    "django": {
        "build": None,
        "test": "python manage.py test || true",
        "start": "gunicorn"
    },

    # ---------------- JAVA ----------------

    "spring": {
        "build": "mvn clean install",
        "test": "mvn test || true",
        "start": "java -jar"
    },

    # ---------------- PHP ----------------

    "laravel": {
        "build": "composer install",
        "test": "php artisan test || true",
        "start": "php artisan serve"
    },

    "symfony": {
        "build": "composer install",
        "test": "php bin/phpunit || true",
        "start": "symfony serve"
    }
}