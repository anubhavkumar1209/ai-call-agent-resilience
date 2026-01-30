# src/logging/logger.py

import os
import json
import logging
from datetime import datetime
from src.config import Config


class JsonLineFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # include structured fields if present
        for k in ["service_name", "error_category", "retry_count", "circuit_state"]:
            if hasattr(record, k):
                data[k] = getattr(record, k)
        return json.dumps(data)


class ErrorLogger:
    def __init__(self):
        self.logger = logging.getLogger("ai_call_agent")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not self.logger.handlers:
            os.makedirs(os.path.dirname(Config.LOG_FILE_PATH), exist_ok=True)
            fh = logging.FileHandler(Config.LOG_FILE_PATH, encoding="utf-8")
            fh.setFormatter(JsonLineFormatter())
            fh.setLevel(logging.INFO)

            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter("%(message)s"))

            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        self.google_sheets_enabled = Config.GOOGLE_SHEETS_ENABLED
        if self.google_sheets_enabled:
            self._setup_google_sheets()

    def _setup_google_sheets(self):
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials

            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(Config.GOOGLE_SHEETS_CREDENTIALS, scope)
            client = gspread.authorize(creds)
            self.sheet = client.open(Config.GOOGLE_SHEETS_NAME).sheet1
        except Exception as e:
            self.logger.error(f"Google Sheets setup failed: {str(e)}")
            self.google_sheets_enabled = False

    def log_error(self, service_name, error_category, message, retry_count, circuit_state):
        self.logger.error(
            message,
            extra={
                "service_name": service_name,
                "error_category": error_category,
                "retry_count": retry_count,
                "circuit_state": circuit_state,
            },
        )

        if self.google_sheets_enabled:
            try:
                self.sheet.append_row([
                    datetime.now().isoformat(),
                    service_name,
                    error_category,
                    message,
                    retry_count,
                    circuit_state
                ])
            except Exception as e:
                self.logger.error(f"Failed to log to Google Sheets: {str(e)}")

    def log_event(self, service_name, message, circuit_state="CLOSED"):
        self.logger.info(
            message,
            extra={
                "service_name": service_name,
                "circuit_state": circuit_state,
            }
        )
