# src/alerts/alert_manager.py

import logging
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config

logger = logging.getLogger("ai_call_agent")


class AlertManager:
    def __init__(self):
        self.email_enabled = Config.EMAIL_ENABLED
        self.telegram_enabled = Config.TELEGRAM_ENABLED
        self.webhook_enabled = Config.WEBHOOK_ENABLED

    def send_alert(self, subject, message, alert_type="ERROR", service_name="UNKNOWN"):
        payload_message = (
            f"[{alert_type}] Service: {service_name}\n"
            f"Time: {datetime.now().isoformat()}\n\n"
            f"{message}"
        )
        logger.info(f"Sending alert: {subject}")

        if self.email_enabled:
            self._send_email(subject, payload_message)
        if self.telegram_enabled:
            self._send_telegram(f"{subject}\n\n{payload_message}")
        if self.webhook_enabled:
            self._send_webhook(subject, payload_message, alert_type, service_name)

    def _send_email(self, subject, message):
        try:
            msg = MIMEMultipart()
            msg["From"] = Config.EMAIL_FROM
            msg["To"] = Config.EMAIL_TO
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(Config.EMAIL_FROM, Config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Email alert failed: {str(e)}")

    def _send_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        except Exception as e:
            logger.error(f"Telegram alert failed: {str(e)}")

    def _send_webhook(self, subject, message, alert_type, service_name):
        try:
            requests.post(
                Config.WEBHOOK_URL,
                json={
                    "subject": subject,
                    "message": message,
                    "alert_type": alert_type,
                    "service_name": service_name,
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Webhook alert failed: {str(e)}")
