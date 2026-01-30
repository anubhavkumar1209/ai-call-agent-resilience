# src/main.py

import time
import logging
from src.logging.logger import ErrorLogger
from src.alerts.alert_manager import AlertManager
from src.retry.retry_handler import RetryHandler
from src.circuit_breaker.circuit_breaker import CircuitBreaker
from src.health_check.health_checker import HealthChecker
from src.services.elevenlabs_service import ElevenLabsService
from src.services.llm_service import LLMService
from src.exceptions.custom_exceptions import CircuitBreakerOpenError, TransientError, PermanentError

logger = logging.getLogger("ai_call_agent")


class AICallAgent:
    def __init__(self):
        self.error_logger = ErrorLogger()
        self.alert_manager = AlertManager()
        self.retry_handler = RetryHandler()

        self.elevenlabs = ElevenLabsService()
        self.llm = LLMService()

        # Circuit breaker OPEN alert hook
        def on_cb_open(service_name):
            self.alert_manager.send_alert(
                subject=f"Circuit Breaker OPEN: {service_name}",
                message=f"Circuit breaker opened for {service_name}. Fail-fast enabled.",
                alert_type="CRITICAL",
                service_name=service_name
            )
            self.error_logger.log_error(
                service_name=service_name,
                error_category="CIRCUIT_BREAKER_OPEN",
                message="Circuit breaker opened",
                retry_count=0,
                circuit_state="OPEN"
            )

        self.elevenlabs_cb = CircuitBreaker("ElevenLabs", on_open=on_cb_open)
        self.llm_cb = CircuitBreaker("LLM", on_open=on_cb_open)

        # Health checkers must include alert_manager for dependency-down alerts
        self.elevenlabs_health = HealthChecker(self.elevenlabs, self.elevenlabs_cb, self.alert_manager)
        self.llm_health = HealthChecker(self.llm, self.llm_cb, self.alert_manager)

        self.contact_queue = [
            {"id": 1, "name": "Contact 1", "phone": "+1234567890"},
            {"id": 2, "name": "Contact 2", "phone": "+1234567891"},
            {"id": 3, "name": "Contact 3", "phone": "+1234567892"},
        ]

    def start(self):
        logger.info("Starting AI Call Agent")
        self.elevenlabs_health.start()
        self.llm_health.start()
        self.process_contact_queue()

    def stop(self):
        logger.info("Stopping AI Call Agent")
        self.elevenlabs_health.stop()
        self.llm_health.stop()

    def process_contact_queue(self):
        for contact in self.contact_queue:
            logger.info("\n" + "=" * 50)
            logger.info(f"Processing contact: {contact['name']}")

            try:
                self.make_call(contact)
                logger.info(f"Successfully processed {contact['name']}")

            # Graceful degradation
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open for {e.service_name}. Skipping contact.")
                self.error_logger.log_error(
                    service_name=e.service_name,
                    error_category="CIRCUIT_BREAKER_OPEN",
                    message=str(e),
                    retry_count=0,
                    circuit_state=self.get_circuit_state(e.service_name),
                )
                continue

            except TransientError as e:
                retry_count = getattr(e, "retry_count", 0)
                logger.error(f"Transient error for {contact['name']}: {e.message}")

                self.error_logger.log_error(
                    service_name=e.service_name,
                    error_category="TRANSIENT_ERROR",
                    message=e.message,
                    retry_count=retry_count,
                    circuit_state=self.get_circuit_state(e.service_name),
                )

                self.alert_manager.send_alert(
                    subject=f"Call Failed for {contact['name']}",
                    message=f"Transient error: {e.message} (retries={retry_count})",
                    alert_type="ERROR",
                    service_name=e.service_name
                )
                continue

            except PermanentError as e:
                logger.error(f"Permanent error for {contact['name']}: {e.message}")

                self.error_logger.log_error(
                    service_name=e.service_name,
                    error_category="PERMANENT_ERROR",
                    message=e.message,
                    retry_count=0,
                    circuit_state=self.get_circuit_state(e.service_name),
                )

                self.alert_manager.send_alert(
                    subject=f"Permanent Failure for {contact['name']}",
                    message=f"Permanent error: {e.message}",
                    alert_type="CRITICAL",
                    service_name=e.service_name
                )
                continue

            except Exception as e:
                logger.error(f"Unexpected error for {contact['name']}: {str(e)}")
                continue

            time.sleep(2)

    def make_call(self, contact):
        logger.info("Step 1: Generating response with LLM")
        llm_response = self.call_with_resilience(
            service=self.llm,
            circuit_breaker=self.llm_cb,
            method_name="generate_response",
            prompt=f"Generate greeting for {contact['name']}"
        )

        logger.info("Step 2: Converting text to speech with ElevenLabs")
        _audio = self.call_with_resilience(
            service=self.elevenlabs,
            circuit_breaker=self.elevenlabs_cb,
            method_name="text_to_speech",
            text=llm_response.get("response", "Hello")
        )

        logger.info(f"Call completed successfully for {contact['name']}")

    def call_with_resilience(self, service, circuit_breaker, method_name, **kwargs):
        def service_call():
            method = getattr(service, method_name)
            return circuit_breaker.call(method, **kwargs)

        result, retry_count = self.retry_handler.execute_with_retry(service_call)

        # If you want: log success events too (optional)
        # self.error_logger.log_event(service.name, f"Call success {method_name}", circuit_breaker.get_state())

        return result

    def get_circuit_state(self, service_name):
        if service_name == "ElevenLabs":
            return self.elevenlabs_cb.get_state()
        if service_name == "LLM":
            return self.llm_cb.get_state()
        return "UNKNOWN"


def main():
    agent = AICallAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        agent.stop()
        logger.info("AI Call Agent stopped")


if __name__ == "__main__":
    main()
