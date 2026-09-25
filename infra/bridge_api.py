from flask import Flask, request, jsonify, send_file, Response
import os
import subprocess
import shutil
from pathlib import Path
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Simple token for authentication (in production, use a proper secret)
API_TOKEN = os.getenv("ONBOARD_API_TOKEN", "changeme")

def require_token():
    token = request.headers.get('X-API-Key')
    if token != API_TOKEN:
        return False
    return True

BASE_DIR = Path("/home/ubuntu/.hermes/businesses")
TEMPLATE_CONFIG = Path("/home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/config.yaml.template")
WHATSAPP_BOT_QR_URL = "http://127.0.0.1:8080/qr"  # WhatsApp bot running on same machine

@app.route('/onboard', methods=['POST'])
def onboard():
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    business_id = data.get('businessId')
    if not business_id:
        return jsonify({"error": "businessId required"}), 400
    name = data.get('name', '')
    category = data.get('category', '')
    timezone = data.get('timezone', 'Asia/Kolkata')
    workingHoursStart = data.get('workingHoursStart', '09:00')
    workingHoursEnd = data.get('workingHoursEnd', '18:00')
    # Create business directory
    biz_dir = BASE_DIR / business_id
    config_dir = biz_dir / "config"
    media_dir = biz_dir / "media"
    config_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    # Copy template config and replace placeholder
    if TEMPLATE_CONFIG.exists():
        config_content = TEMPLATE_CONFIG.read_text()
        config_content = config_content.replace("{{business_id}}", business_id)
        (config_dir / "config.yaml").write_text(config_content)
    else:
        return jsonify({"error": "Template config not found"}), 500
    # Create placeholder session and calendar creds if not exist
    session_file = biz_dir / "session.json"
    if not session_file.exists():
        session_file.write_text('{}')
    creds_file = config_dir / "calendar_credentials.json"
    if not creds_file.exists():
        creds_file.write_text('{}')
    # Start the agent via PM2
    daemon_path = "/home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/daemon.py"
    # Use subprocess to start the process; we detach it so the API can return quickly
    try:
        subprocess.Popen([
            "pm2", "start", daemon_path,
            "--name", f"whatsapp-{business_id}",
            "--interpreter", "python3",
            "--", business_id
        ])
        # Save PM2 list
        subprocess.run(["pm2", "save"], check=False)
    except Exception as e:
        return jsonify({"error": f"Failed to start agent: {str(e)}"}), 500
    return jsonify({"success": True, "message": f"Business {business_id} onboarded."})

@app.route('/verify-session/<business_id>', methods=['GET'])
def verify_session(business_id):
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    session_file = BASE_DIR / business_id / "session.json"
    if not session_file.exists():
        return jsonify({"valid": False, "reason": "Session file not found"})
    try:
        content = session_file.read_text()
        # Simple check: not empty and valid JSON
        if content.strip() == '' or content.strip() == '{}':
            return jsonify({"valid": False, "reason": "Session file is empty or placeholder"})
        # Optionally, we could try to parse JSON to ensure it's valid
        json.loads(content)
        return jsonify({"valid": True})
    except Exception as e:
        return jsonify({"valid": False, "reason": f"Invalid session: {str(e)}"})

@app.route('/qr', methods=['GET'])
def get_qr():
    # Proxy the QR code from the WhatsApp bot to avoid mixed content issues
    try:
        import requests
        response = requests.get(WHATSAPP_BOT_QR_URL, timeout=5)
        if response.status_code == 200:
            # Return the image with appropriate content type
            return Response(response.content, content_type=response.headers.get('Content-Type', 'image/png'))
        else:
            return jsonify({"error": "Failed to fetch QR code from WhatsApp bot"}), 500
    except Exception as e:
        return jsonify({"error": f"Error fetching QR code: {str(e)}"}), 500

@app.route('/status/<business_id>', methods=['GET'])
def get_status(business_id):
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    # Use PM2 to get the status of the specific agent
    try:
        result = subprocess.run(["pm2", "describe", f"whatsapp-{business_id}"], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output to get status (simplified: just check if it's online)
            output = result.stdout
            if "status            │ online" in output:
                return jsonify({"status": "online", "details": output})
            else:
                return jsonify({"status": "offline or errored", "details": output})
        else:
            return jsonify({"error": f"Failed to get status: {result.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error getting status: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)