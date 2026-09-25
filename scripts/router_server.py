"""
WhatsApp Router Server - Flask app on port 8082
Handles incoming messages from whatsapp-bot and routes to restaurant router
"""
import os
import sys
from pathlib import Path

# Load .env file FIRST - before anything else
try:
    from dotenv import load_dotenv
    # Force override to ensure we get the latest value
    load_dotenv("/home/ubuntu/.hermes/.env", override=True)
except Exception as e:
    print(f"Warning: Could not load .env: {e}")
    pass

# Debug: print the loaded value
print(f"DEBUG: ONBOARD_API_TOKEN = {repr(os.getenv('ONBOARD_API_TOKEN'))}")

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from flask import Flask, request, jsonify
import asyncio
import threading
from init import get_manager

app = Flask(__name__)

# Store managers per business_id (created on first request)
_managers = {}
_managers_lock = threading.Lock()

API_KEY = os.getenv("ONBOARD_API_TOKEN", "")

print(f"API_KEY loaded: {API_KEY[:10]}..." if API_KEY else "No API_KEY loaded")

def check_auth(req):
    """Check X-API-Key header"""
    if not API_KEY:
        return True  # No auth configured, allow all (dev mode)
    return req.headers.get("X-API-Key") == API_KEY

async def get_manager_async(business_id: str):
    """Get or create manager for business_id"""
    with _managers_lock:
        if business_id not in _managers:
            _managers[business_id] = get_manager(business_id)
            await _managers[business_id].start()
        return _managers[business_id]

@app.route("/health", methods=["GET", "POST"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "whatsapp-router"}), 200

@app.route("/message", methods=["POST"])
def handle_message():
    """Process incoming WhatsApp message"""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        business_id = data.get("business_id")
        from_number = data.get("from")
        text = data.get("text")
        msg_id = data.get("msg_id")

        if not all([business_id, from_number, text, msg_id]):
            return jsonify({"error": "Missing required fields: business_id, from, text, msg_id"}), 400

        # Get manager and process message
        manager = asyncio.run(get_manager_async(business_id))
        result = asyncio.run(manager.process_incoming_message(from_number, text, msg_id))

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/stats/<business_id>", methods=["GET"])
def get_stats(business_id):
    """Get stats for a business"""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        manager = asyncio.run(get_manager_async(business_id))
        stats = manager.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_server():
    """Run Flask server"""
    app.run(host="0.0.0.0", port=8082, threaded=True)

if __name__ == "__main__":
    run_server()