from flask import Flask, request, jsonify, send_file, Response
import os
import re
import time
import subprocess
import shutil
from pathlib import Path
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Simple token for authentication (in production, use a proper secret)
API_TOKEN = os.getenv("ONBOARD_API_TOKEN", "changeme")

def require_token():
    token = request.headers.get('X-API-Key')
    # Debug: print token and API_TOKEN (masking for security)
    if token:
        masked_token = token[:3] + '...' + token[-3:] if len(token) > 6 else '*' * 6
        print(f"DEBUG: require_token - token header: {masked_token}")
    else:
        print("DEBUG: require_token - no token header")
    masked_api = API_TOKEN[:3] + '...' + API_TOKEN[-3:] if len(API_TOKEN) > 6 else '*' * 6
    print(f"DEBUG: require_token - API_TOKEN: {masked_api}")
    if token != API_TOKEN:
        return False
    return True

BASE_DIR = Path("/home/ubuntu/.hermes/businesses")
TEMPLATE_CONFIG = Path("/home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/config.yaml.template")
WHATSAPP_BOT_QR_URL = "http://127.0.0.1:8080/qr"  # WhatsApp bot running on same machine
BOT_URL = "http://127.0.0.1:8080"
LEADS_DIR = Path("/home/ubuntu/.hermes/leads")
PHONE_MAP_FILE = Path("/home/ubuntu/.hermes/phone_map.json")
SCHEMA_SQL = Path("/home/ubuntu/rivox-services/infra/schema.sql")
PG_PASSWORD = "secure_password"
PM2 = "/home/ubuntu/.local/bin/pm2"

KNOWN_SERVICES = {"table_booking", "food_order", "party_booking", "normal_chat"}


def yaml_str(value):
    """Make a string safe for double-quoted YAML."""
    return str(value or "").replace("\\", "").replace('"', "'").replace("\n", " ").replace("\r", " ")


def bot_call(path, method="GET", timeout=8):
    try:
        if method == "POST":
            r = requests.post(BOT_URL + path, timeout=timeout)
        else:
            r = requests.get(BOT_URL + path, timeout=timeout)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {"raw": r.text[:200]}
    except Exception as e:
        return 502, {"error": str(e)}


def update_phone_map(phone_number, business_id):
    digits = re.sub(r"\D", "", str(phone_number or ""))
    if not digits:
        return
    pm = {}
    if PHONE_MAP_FILE.exists():
        try:
            pm = json.loads(PHONE_MAP_FILE.read_text())
        except Exception:
            pm = {}
    pm["+" + digits] = business_id
    PHONE_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    PHONE_MAP_FILE.write_text(json.dumps(pm, indent=2))


def inject_config(config_path, data, business_id):
    """Fill template config with submitted portal data."""
    cfg = config_path.read_text()

    name = yaml_str(data.get("name") or business_id)
    cfg = cfg.replace('name: ""  # e.g., "Glow Beauty Salon"', f'name: "{name}"')

    category = yaml_str(data.get("category") or "general")
    cfg = cfg.replace('type: "general"  # restaurant, salon, clinic, gym, etc.', f'type: "{category}"')

    owner = yaml_str(data.get("ownerWhatsApp") or data.get("phoneNumber") or "")
    cfg = cfg.replace('owner_whatsapp: ""', f'owner_whatsapp: "{owner}"')

    # enabled_services block
    chosen = []
    for s in (data.get("services") or []):
        if s in KNOWN_SERVICES and s not in chosen:
            chosen.append(s)
    if not chosen:
        chosen = ["normal_chat"]
    lines = "    enabled_services:\n" + "".join(f"      - {s}\n" for s in chosen) + "    tables: 10"
    cfg = re.sub(r"    enabled_services:\n(?:      - .*\n)+    tables: 10", lines, cfg, count=1)

    # FAQ block (restaurant.faq) — inserted after feedback.thankyou line
    address = yaml_str(data.get("address") or "")
    loc_ans = f"Our address is: {address}." if address else "Message us here for our location."
    faq_block = (
        '      thankyou_message: "Thank you for your feedback! We appreciate your support."\n'
        "    faq:\n"
        '      - question: "What are your timings?"\n'
        '        answer: "We are open from 09:00 to 18:00 daily."\n'
        '      - question: "Where are you located?"\n'
        f'        answer: "{loc_ans}"\n'
        '      - question: "How do I pay?"\n'
        '        answer: "We accept cash and UPI payments."\n'
    )
    anchor = '      thankyou_message: "Thank you for your feedback! We appreciate your support."\n'
    if anchor in cfg and "    faq:" not in cfg:
        cfg = cfg.replace(anchor, faq_block, 1)

    config_path.write_text(cfg)


def create_business_db(business_id):
    db_name = f"whatsapp_business_{business_id}"
    if not re.fullmatch(r"[a-z0-9_]{3,50}", business_id or ""):
        return False
    try:
        r = subprocess.run(
            ["sudo", "-u", "postgres", "psql", "-c", f"CREATE DATABASE {db_name} OWNER agency_user"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            print(f"DB create: {r.stderr.strip()[:200]}")
            return False
        if SCHEMA_SQL.exists():
            env = dict(os.environ)
            env["PGPASSWORD"] = PG_PASSWORD
            s = subprocess.run(
                ["psql", "-U", "agency_user", "-h", "localhost", "-d", db_name, "-f", str(SCHEMA_SQL)],
                capture_output=True, text=True, timeout=60, env=env,
            )
            print(f"schema apply rc={s.returncode} {s.stderr.strip()[:200]}")
        return True
    except Exception as e:
        print(f"create_business_db error: {e}")
        return False


def write_lead(data, business_id):
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    lead = {
        "leadId": f"lead_{business_id}_{int(time.time())}",
        "businessId": business_id,
        "source": data.get("source") or "portal_v2",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "leadName": data.get("leadName") or "",
        "businessName": data.get("name") or "",
        "category": data.get("category") or "",
        "categoryOther": data.get("categoryOther") or "",
        "address": data.get("address") or "",
        "specialties": data.get("specialties") or "",
        "customNote": data.get("customNote") or "",
        "phoneNumber": data.get("phoneNumber") or "",
        "ownerWhatsApp": data.get("ownerWhatsApp") or "",
        "services": data.get("services") or [],
        "payment": {"status": "pending", "amount": "2000", "upi": "rivox@upi"},
        "setup": {"status": "started", "pm2": f"whatsapp-{business_id}"},
    }
    (LEADS_DIR / f"{business_id}.json").write_text(json.dumps(lead, indent=2))
    return lead


@app.route('/reset-session', methods=['POST'])
def reset_session():
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    status, info = bot_call("/reset", method="POST", timeout=25)
    if status >= 500:
        return jsonify({"error": info.get("error", "Bot not reachable")}), 502
    return jsonify({"success": bool(info.get("success")), "detail": info}), 200


@app.route('/verify-phone/<phone>', methods=['GET'])
def verify_phone(phone):
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    entered = re.sub(r"\D", "", phone or "")
    status, info = bot_call("/whoami", timeout=6)
    if status != 200 or "error" in info:
        return jsonify({"valid": False, "reason": "Bot not reachable"}), 200
    if not info.get("connected") or not info.get("number"):
        return jsonify({"valid": False, "reason": "QR not scanned yet"}), 200
    conn = re.sub(r"\D", "", info.get("number") or "")
    ok = bool(entered) and (
        entered == conn
        or (len(entered) >= 10 and len(conn) >= 10 and entered[-10:] == conn[-10:])
    )
    return jsonify({"valid": ok, "number": info.get("number")}), 200


@app.route('/lead-status/<business_id>', methods=['GET'])
def lead_status(business_id):
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    f = LEADS_DIR / f"{business_id}.json"
    if not f.exists():
        return jsonify({"error": "Lead not found"}), 404
    return jsonify(json.loads(f.read_text())), 200


@app.route('/approve/<business_id>', methods=['POST'])
def approve(business_id):
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    f = LEADS_DIR / f"{business_id}.json"
    if not f.exists():
        return jsonify({"error": "Lead not found"}), 404
    lead = json.loads(f.read_text())
    lead.setdefault("payment", {})["status"] = "paid"
    lead["payment"]["paidAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    lead["status"] = "active"
    f.write_text(json.dumps(lead, indent=2))
    return jsonify({"success": True, "businessId": business_id, "status": "active"}), 200


@app.route('/onboard', methods=['POST'])
def onboard():
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    business_id = data.get('businessId')
    if not business_id:
        return jsonify({"error": "businessId required"}), 400
    if not re.fullmatch(r"[a-z0-9_]{3,50}", business_id):
        return jsonify({"error": "businessId must match [a-z0-9_]{3,50}"}), 400
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
    # Portal V2: fill config with submitted form data
    try:
        inject_config(config_dir / "config.yaml", data, business_id)
    except Exception as e:
        print(f"inject_config error: {e}")
    # Create placeholder session and calendar creds if not exist
    session_file = biz_dir / "session.json"
    if not session_file.exists():
        session_file.write_text('{}')
    creds_file = config_dir / "calendar_credentials.json"
    if not creds_file.exists():
        creds_file.write_text('{}')
    # Lead record (Hermes + owner watch this) + phone map (bot routes by connected number)
    try:
        write_lead(data, business_id)
    except Exception as e:
        print(f"write_lead error: {e}")
    try:
        update_phone_map(data.get('phoneNumber') or data.get('ownerWhatsApp'), business_id)
    except Exception as e:
        print(f"phone_map error: {e}")
    # Per-business Postgres DB (fresh DB only gets schema)
    create_business_db(business_id)
    # Start the agent via PM2
    daemon_path = "/home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/daemon.py"
    # Use subprocess to start the process; we detach it so the API can return quickly
    try:
        subprocess.Popen([
            PM2, "start", daemon_path,
            "--name", f"whatsapp-{business_id}",
            "--interpreter", "python3",
            "--", business_id
        ])
        # Save PM2 list
        subprocess.run([PM2, "save"], check=False)
    except Exception as e:
        return jsonify({"error": f"Failed to start agent: {str(e)}"}), 500
    return jsonify({
        "success": True,
        "businessId": business_id,
        "message": f"Business {business_id} onboarded. Lead saved — payment pending.",
    })

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
        result = subprocess.run([PM2, "describe", f"whatsapp-{business_id}"], capture_output=True, text=True)
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
