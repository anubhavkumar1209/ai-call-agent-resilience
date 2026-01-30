# src/health_check/health_checker.py

import time
import threading
import logging
from src.config import Config

logger = logging.getLogger("ai_call_agent")


class HealthChecker:
    def __init__(self, service, circuit_breaker, alert_manager, check_interval=None, down_threshold_checks=None):
        self.service = service
        self.circuit_breaker = circuit_breaker
        self.alert_manager = alert_manager

        self.check_interval = check_interval if check_interval is not None else Config.HEALTH_CHECK_INTERVAL
        self.down_threshold_checks = down_threshold_checks if down_threshold_checks is not None else Config.DEPENDENCY_DOWN_THRESHOLD_CHECKS

        self.running = False
        self.thread = None
        self.consecutive_down = 0
        self.sent_down_alert = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Health checker started for {self.service.name}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info(f"Health checker stopped for {self.service.name}")

    def _run(self):
        while self.running:
            try:
                ok = self.service.health_check()

                if ok:
                    logger.info(f"{self.service.name} is healthy")
                    self.consecutive_down = 0
                    self.sent_down_alert = False

                    # Auto recovery: reset circuit if open and service is healthy again
                    if self.circuit_breaker.get_state() == "OPEN":
                        logger.info(f"Resetting circuit breaker for {self.service.name}")
                        self.circuit_breaker.reset()

                else:
                    self.consecutive_down += 1
                    logger.warning(f"{self.service.name} is unhealthy (count={self.consecutive_down})")

                    # requirement: alert if dependency stays down beyond threshold
                    if (not self.sent_down_alert) and (self.consecutive_down >= self.down_threshold_checks):
                        self.sent_down_alert = True
                        self.alert_manager.send_alert(
                            subject=f"Dependency Down: {self.service.name}",
                            message=f"{self.service.name} unhealthy for {self.consecutive_down} checks.",
                            alert_type="CRITICAL",
                            service_name=self.service.name
                        )

            except Exception as e:
                logger.error(f"Health check failed for {self.service.name}: {str(e)}")

            time.sleep(self.check_interval)
