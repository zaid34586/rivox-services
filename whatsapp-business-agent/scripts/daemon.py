"""
WhatsApp Business Agent Daemon Runner
"""
import asyncio
import signal
import sys
import os
from pathlib import Path

scripts_dir = Path(__file__).parent
os.chdir(scripts_dir)
sys.path.insert(0, str(scripts_dir))
from init import get_manager

# Determine business_id from command line argument, environment variable, or default
if len(sys.argv) > 1:
    business_id = sys.argv[1]
else:
    business_id = os.getenv("WHATSAPP_BUSINESS_ID", "default")

async def main():
    manager = get_manager(business_id)
    await manager.start()
    try:
        # Keep alive until stopped
        while True:
            await asyncio.sleep(3600)
    finally:
        await manager.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
