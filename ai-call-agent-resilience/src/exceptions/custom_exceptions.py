# src/exceptions/custom_exceptions.py

class AppError(Exception):
    """Base application exception."""
    def __init__(self, service_name: str, message: str = "Error"):
        super().__init__(message)
        self.service_name = service_name
        self.message = message


class TransientError(AppError):
    """Retryable errors: timeouts, 503, network failures."""
    def __init__(self, service_name: str, message: str = "Transient error", retry_count: int = 0):
        super().__init__(service_name, message)
        self.retry_count = retry_count


class PermanentError(AppError):
    """Non-retryable errors: 401, invalid payload, quota exceeded."""
    pass


class CircuitBreakerOpenError(AppError):
    """Raised when circuit breaker is open and fail-fast happens."""
    def __init__(self, service_name: str):
        super().__init__(service_name, f"Circuit breaker is OPEN for {service_name}")
