# WhatsApp Business Agent - Main Entry Point & CLI
import asyncio
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

# Import modules directly
import provider_registry
import health_monitor
import router
import reporter


class WhatsAppBusinessAgentManager:
    """Main entry point for WhatsApp Business Agent."""
    
    def __init__(self, business_id: str = "default"):
        self.business_id = business_id
        self.provider_registry = provider_registry.get_provider_registry(business_id)
        self.router = router.Router(self.provider_registry)
        self.health_monitor = health_monitor.HealthMonitor()
        self.reporter = reporter.Reporter(self)
        self._running = False
    
    async def start(self):
        """Start background processing."""
        if self._running:
            return
        self._running = True
        await self.health_monitor.start()
        await self.router.start_background_tasks()
        print(f"WhatsAppBusinessAgentManager started for business: {self.business_id}")
    
    async def stop(self):
        """Stop background processing."""
        self._running = False
        await self.health_monitor.stop()
        await self.router.stop_background_tasks()
        print(f"WhatsAppBusinessAgentManager stopped for business: {self.business_id}")
    
    async def process_incoming_message(self, sender: str, message: str, message_id: str) -> Dict[str, Any]:
        """Process incoming WhatsApp message"""
        return await self.router.handle_incoming_message(sender, message, message_id)
    
    async def schedule_appointment(self, title: str, description: str, start_time: datetime, 
                                 end_time: datetime, attendee_info: Dict[str, Any]) -> bool:
        """Schedule appointment via calendar integration"""
        return await self.router.schedule_appointment(title, description, start_time, end_time, attendee_info)
    
    async def send_reminder(self, appointment_id: str, reminder_type: str) -> bool:
        """Send appointment reminder"""
        return await self.router.send_reminder(appointment_id, reminder_type)
    
    async def request_review(self, customer_id: str, service_details: Dict[str, Any]) -> bool:
        """Request review from customer"""
        return await self.router.request_review(customer_id, service_details)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.router.get_stats()
    
    def print_status(self):
        """Print live status dashboard."""
        print(self.reporter.generate_status_report())
    
    def print_daily_report(self):
        """Print daily report."""
        print(self.reporter.generate_daily_report())


# Global instance dictionary (one per business)
_managers = {}

def get_manager(business_id: str = "default") -> WhatsAppBusinessAgentManager:
    """Get or create manager instance for a business"""
    if business_id not in _managers:
        _managers[business_id] = WhatsAppBusinessAgentManager(business_id)
    return _managers[business_id]


# CLI Commands
async def cmd_status(business_id: str = "default"):
    """CLI: Show status dashboard for a business."""
    manager = get_manager(business_id)
    manager.print_status()

def cmd_report(business_id: str = "default"):
    """CLI: Show daily report for a business."""
    manager = get_manager(business_id)
    manager.print_daily_report()

def cmd_stats(business_id: str = "default"):
    """CLI: Show statistics for a business."""
    manager = get_manager(business_id)
    stats = manager.get_stats()
    print(f"Business: {business_id}")
    print(f"Messages processed: {stats.get('messages_processed', 0)}")
    print(f"Appointments scheduled: {stats.get('appointments_scheduled', 0)}")
    print(f"Reminders sent: {stats.get('reminders_sent', 0)}")
    print(f"Reviews requested: {stats.get('reviews_requested', 0)}")

async def cmd_test(business_id: str = "default"):
    """CLI: Test agent health check."""
    manager = get_manager(business_id)
    health = manager.health_monitor.get_stats(60)
    print(f"Business: {business_id}")
    print(f"Health Checks (last hour): {health.get('checks', 0)}")
    print(f"Avg Success Rate: {health.get('avg_success_rate', 0):.1%}")
    print(f"Alerts Triggered: {health.get('alerts_triggered', 0)}")

if __name__ == "__main__":
    async def main():
        COMMANDS = ("status", "report", "stats", "test", "process")
        argv = sys.argv[1:]

        # Canonical: init.py <command> <business_id> [args...]
        # Legacy:    init.py <business_id> <command> [args...]
        if argv and argv[0] in COMMANDS:
            cmd = argv[0]
            rest = argv[1:]
        elif argv and len(argv) > 1 and argv[1] in COMMANDS:
            cmd = argv[1]
            rest = [argv[0]] + argv[2:]
        elif argv:
            cmd = "status"
            rest = argv
        else:
            cmd = "status"
            rest = []

        business_id = rest[0] if rest else "default"
        args = rest[1:]

        manager = get_manager(business_id)
        await manager.start()
        try:
            if cmd == "status":
                manager.print_status()
            elif cmd == "report":
                manager.print_daily_report()
            elif cmd == "stats":
                s = manager.get_stats()
                print(f"Business: {business_id}")
                print(f"Messages processed: {s.get('messages_processed', 0)}")
                print(f"Restaurant welcomes: {s.get('restaurant_welcome_sent', 0)}")
                print(f"Restaurant bookings: {s.get('restaurant_bookings_created', 0)}")
                print(f"Appointments scheduled: {s.get('appointments_scheduled', 0)}")
                print(f"Reminders sent: {s.get('reminders_sent', 0)}")
            elif cmd == "test":
                health = manager.health_monitor.get_stats(60)
                print(f"Business: {business_id}")
                print(f"Health Checks (last hour): {health.get('checks', 0)}")
                print(f"Avg Success Rate: {health.get('avg_success_rate', 0):.1%}")
            elif cmd == "process":
                sender = args[0] if len(args) > 0 else "+919876543210"
                message = args[1] if len(args) > 1 else "Hello, I want to book an appointment"
                message_id = args[2] if len(args) > 2 else "test_001"
                result = await manager.process_incoming_message(sender, message, message_id)
                print(f"Processing result: {result}")
            else:
                print("Commands: status, report, stats, test, process")
        finally:
            await manager.stop()

    asyncio.run(main())
