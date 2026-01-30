# src/config.py

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Retry Configuration
    INITIAL_RETRY_DELAY = 5  # seconds
    MAX_RETRY_ATTEMPTS = 3
    BACKOFF_MULTIPLIER = 2

    # Circuit Breaker Configuration
    FAILURE_THRESHOLD = 3
    SUCCESS_THRESHOLD = 2
    TIMEOUT = 30  # seconds

    # Health check
    HEALTH_CHECK_INTERVAL = 10  # seconds
    DEPENDENCY_DOWN_THRESHOLD_CHECKS = 3  # alert after 3 consecutive failed checks

    # Logging
    LOG_FILE_PATH = "logs/error_recovery.jsonl"
    GOOGLE_SHEETS_ENABLED = False
    GOOGLE_SHEETS_CREDENTIALS = "credentials.json"
    GOOGLE_SHEETS_NAME = "AI Call Agent Logs"

    # Alerts
    EMAIL_ENABLED = False
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

    TELEGRAM_ENABLED = False
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    WEBHOOK_ENABLED = False
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

    # Service URLs (mock)
    ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    LLM_URL = "https://api.openai.com/v1/chat/completions"
