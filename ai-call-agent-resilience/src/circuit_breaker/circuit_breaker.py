# src/circuit_breaker/circuit_breaker.py

import time
import threading
import logging
from enum import Enum
from src.config import Config
from src.exceptions.custom_exceptions import CircuitBreakerOpenError, TransientError, PermanentError

logger = logging.getLogger("ai_call_agent")


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, service_name, failure_threshold=None, success_threshold=None, timeout=None, on_open=None):
        self.service_name = service_name
        self.failure_threshold = int(failure_threshold if failure_threshold is not None else Config.FAILURE_THRESHOLD)
        self.success_threshold = int(success_threshold if success_threshold is not None else Config.SUCCESS_THRESHOLD)
        self.timeout = float(timeout if timeout is not None else Config.TIMEOUT)

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()

        # callback: on_open(service_name)
        self.on_open = on_open

    def get_state(self):
        return self.state.value

    def call(self, func, *args, **kwargs):
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset_locked():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for {self.service_name}")
                else:
                    raise CircuitBreakerOpenError(self.service_name)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except (TransientError, PermanentError):
            self._on_failure()
            raise

    def _should_attempt_reset_locked(self):
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.timeout

    def _on_success(self):
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed_locked()
            else:
                self.failure_count = 0

    def _on_failure(self):
        with self.lock:
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open_locked()
                return

            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open_locked()

    def _transition_to_open_locked(self):
        self.state = CircuitState.OPEN
        self.failure_count = 0
        self.success_count = 0
        logger.error(f"Circuit breaker OPENED for {self.service_name}")

        # Alert hook for requirement: "Send alert when CB opens"
        if self.on_open:
            try:
                self.on_open(self.service_name)
            except Exception:
                pass

    def _transition_to_closed_locked(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker CLOSED for {self.service_name}")

    def reset(self):
        with self.lock:
            self._transition_to_closed_locked()
