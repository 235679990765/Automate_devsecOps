import json

from datetime import datetime


class SecurityLogger:

    def __init__(self):

        self.logs = []

    def log(
        self,
        level,
        category,
        message,
        data=None
    ):

        entry = {

            "timestamp":
                str(datetime.utcnow()),

            "level":
                level,

            "category":
                category,

            "message":
                message,

            "data":
                data or {}
        }

        self.logs.append(entry)

        print(
            f"[{level}] "
            f"[{category}] "
            f"{message}"
        )

    def export(self):

        return self.logs

    def save_json(
        self,
        output_file
    ):

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.logs,
                f,
                indent=2
            )