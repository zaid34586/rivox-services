# WhatsApp Business Agent - Reporter
import time
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class Reporter:
    def __init__(self, manager):
        self.manager = manager

    def generate_status_report(self) -> str:
        """Generate live status dashboard."""
        lines = [
            "=" * 60,
            f"WHATSAPP BUSINESS AGENT - STATUS ({self.manager.business_id})",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        stats = self.manager.get_stats()

        lines.append("BUSINESS METRICS:")
        lines.append(f"  Messages Processed: {stats.get('messages_processed', 0)}")
        lines.append(f"  Auto-replies Sent: {stats.get('auto_replies_sent', 0)}")
        lines.append(f"  Appointments Scheduled: {stats.get('appointments_scheduled', 0)}")
        lines.append(f"  Reminders Sent: {stats.get('reminders_sent', 0)}")
        lines.append(f"  Reviews Requested: {stats.get('reviews_requested', 0)}")
        lines.append(f"  Follow-ups Sent: {stats.get('follow_ups_sent', 0)}")
        lines.append("")

        # Connection status from health monitor
        health_stats = self.manager.health_monitor.get_stats(60)
        lines.append("CONNECTION STATUS:")
        lines.append(f"  WhatsApp: {'✅ Connected' if health_stats.get('whatsapp_connected') else '❌ Disconnected'}")
        lines.append(f"  Calendar: {'✅ Connected' if health_stats.get('calendar_connected') else '❌ Disconnected'}")
        lines.append(f"  Database: {'✅ Connected' if health_stats.get('database_connected') else '❌ Disconnected'}")
        lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def generate_daily_report(self) -> str:
        """Generate daily report."""
        lines = [
            "=" * 60,
            f"WHATSAPP BUSINESS AGENT - DAILY REPORT ({self.manager.business_id})",
            "=" * 60,
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            ""
        ]

        stats = self.manager.get_stats()

        lines.append("DAILY SUMMARY:")
        lines.append(f"  Total Messages: {stats.get('messages_processed', 0)}")
        lines.append(f"  New Appointments: {stats.get('appointments_scheduled', 0)}")
        lines.append(f"  Reminders Sent: {stats.get('reminders_sent', 0)}")
        lines.append(f"  Review Requests: {stats.get('reviews_requested', 0)}")
        lines.append("")

        # Calculate conversion rate if we have data
        messages = stats.get('messages_processed', 0)
        appointments = stats.get('appointments_scheduled', 0)
        if messages > 0:
            conversion_rate = (appointments / messages) * 100
            lines.append(f"  Appointment Conversion Rate: {conversion_rate:.1f}%")
        lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def save_report(self, content: str, report_type: str):
        """Save report to file."""
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = reports_dir / f"{report_type}_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(content)

        print(f"Report saved: {filename}")


# Global instance
_reporter = None


def get_reporter() -> Reporter:
    global _reporter
    if _reporter is None:
        # This would normally be set by the manager
        # For now, return a placeholder
        class DummyReporter:
            def generate_status_report(self):
                return "Reporter not initialized"
            def generate_daily_report(self):
                return "Reporter not initialized"
            def save_report(self, content, report_type):
                pass
        return DummyReporter()
    return _reporter
