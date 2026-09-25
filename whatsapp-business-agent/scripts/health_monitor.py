# WhatsApp Business Agent - Health Monitor
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class HealthStats:
    checks: int = 0
    avg_success_rate: float = 0.0
    avg_cache_hit_rate: float = 0.0
    alerts_triggered: int = 0
    circuit_breaker_open_any: bool = False
    whatsapp_connected: bool = False
    calendar_connected: bool = False
    database_connected: bool = False
    last_whatsapp_ping: Optional[float] = None
    last_calendar_ping: Optional[float] = None
    last_database_ping: Optional[float] = None


class HealthMonitor:
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.stats = HealthStats()
        self.provider_registry = None  # Will be set later
    
    def set_provider_registry(self, provider_registry):
        self.provider_registry = provider_registry
    
    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        while self._running:
            # Check connections
            await self._check_whatsapp_connection()
            await self._check_calendar_connection()
            await self._check_database_connection()
            
            self.stats.checks += 1
            # Simulate some success rate (in real implementation, this would be based on actual checks)
            self.stats.avg_success_rate = min(1.0, self.stats.avg_success_rate * 0.9 + 0.1)
            self.stats.avg_cache_hit_rate = min(1.0, self.stats.avg_cache_hit_rate * 0.9 + 0.05)
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_whatsapp_connection(self):
        """Check if WhatsApp is connected"""
        try:
            if self.provider_registry:
                whatsapp_client = self.provider_registry.get_whatsapp_client()
                # In a real implementation, we would ping the WhatsApp service
                # For now, we'll check if the session file exists
                session_file = self.provider_registry.config["whatsapp"]["session_file"]
                self.stats.whatsapp_connected = os.path.exists(session_file)
                self.stats.last_whatsapp_ping = time.time()
        except Exception as e:
            print(f"Error checking WhatsApp connection: {e}")
            self.stats.whatsapp_connected = False
    
    async def _check_calendar_connection(self):
        """Check if calendar service is connected"""
        try:
            if self.provider_registry and self.provider_registry.config["calendar"]["enabled"]:
                calendar_service = self.provider_registry.get_calendar_service()
                if calendar_service == "simple_db":
                    # Check database connection
                    conn = self.provider_registry.get_database_connection()
                    self.stats.calendar_connected = conn is not None
                    if conn:
                        conn.close()
                elif hasattr(calendar_service, 'events'):
                    # Try a simple calendar operation (like getting calendar list)
                    # For simplicity, we'll just assume it's connected if we got the service
                    self.stats.calendar_connected = calendar_service is not None
                else:
                    self.stats.calendar_connected = False
                self.stats.last_calendar_ping = time.time()
            else:
                self.stats.calendar_connected = True  # Not required if disabled
        except Exception as e:
            print(f"Error checking calendar connection: {e}")
            self.stats.calendar_connected = False
    
    async def _check_database_connection(self):
        """Check if database is connected"""
        try:
            if self.provider_registry:
                conn = self.provider_registry.get_database_connection()
                self.stats.database_connected = conn is not None
                if conn:
                    conn.close()
                self.stats.last_database_ping = time.time()
        except Exception as e:
            print(f"Error checking database connection: {e}")
            self.stats.database_connected = False
    
    def get_stats(self, last_seconds: int = 60) -> Dict[str, Any]:
        return {
            "checks": self.stats.checks,
            "avg_success_rate": self.stats.avg_success_rate,
            "avg_cache_hit_rate": self.stats.avg_cache_hit_rate,
            "alerts_triggered": self.stats.alerts_triggered,
            "circuit_breaker_open_any": self.stats.circuit_breaker_open_any,
            "whatsapp_connected": self.stats.whatsapp_connected,
            "calendar_connected": self.stats.calendar_connected,
            "database_connected": self.stats.database_connected,
            "last_whatsapp_ping": self.stats.last_whatsapp_ping,
            "last_calendar_ping": self.stats.last_calendar_ping,
            "last_database_ping": self.stats.last_database_ping
        }


# Global instance
_monitor = None


def get_health_monitor() -> HealthMonitor:
    global _monitor
    if _monitor is None:
        _monitor = HealthMonitor()
    return _monitor
