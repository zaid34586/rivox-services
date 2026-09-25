# WhatsApp Business Agent - Circuit Breaker
import time
from threading import Lock


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.failure_count = 0
        self.last_failure_time: float = 0
        self._lock = Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.failure_count < self.failure_threshold:
                return True

            if time.time() - self.last_failure_time > self.timeout:
                # Reset after timeout
                self.failure_count = 0
                return True

            return False

    def record_success(self):
        with self._lock:
            self.failure_count = 0

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

    def is_open(self) -> bool:
        with self._lock:
            if self.failure_count >= self.failure_threshold:
                if time.time() - self.last_failure_time <= self.timeout:
                    return True
                else:
                    self.failure_count = 0  # Reset if timeout passed
            return False


# Global instance factory
def get_circuit_breaker(failure_threshold: int = 5, timeout: int = 300) -> CircuitBreaker:
    return CircuitBreaker(failure_threshold, timeout)
