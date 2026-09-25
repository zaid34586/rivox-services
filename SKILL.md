---
name: whatsapp-business-agent
description: Provides WhatsApp automation for local businesses.
category: autonomous-ai-agents
---

# WhatsApp Business Agent - Complete Automation for Local Businesses

## Description
Use when deploying WhatsApp automation for local businesses (restaurants, salons, clinics). Provides auto-reply, booking management, reminders, follow-ups, and review collection via personal WhatsApp Web (Baileys). Each business gets isolated deployment with strong connection to central Hermes infrastructure.

## Core Features
- **Auto-reply Agent**: Instant responses to customer messages using intent detection
- **Booking Manager**: Calendar integration for appointments (Google Calendar/Simple DB)
- **Reminder System**: Automated SMS/WhatsApp reminders before appointments
- **Follow-up Agent**: Post-service check-ins and review requests
- **Review Collector**: Automates feedback collection and public review posting
- **Business Isolation**: Separate DB schemas/config per business; shared agent code
- **Hermes Integration**: Uses Redis (scheduler), PostgreSQL (data), Monitor Agent (health checks)
- **Rivox Monitoring**: Each business agent is monitored by the central Rivox monitor which checks process health, session validity, and sends Telegram alerts on issues via Telegram.

## Procedure
1. **Create business folder**:
   ```bash
   BUSINESS_ID="<your_business_id>"
   mkdir -p /home/ubuntu/.hermes/businesses/$BUSINESS_ID/{config,media}
   ```
2. **Copy and customize config**:
   ```bash
   cp /home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/config.yaml.template
      /home/ubuntu/.hermes/businesses/$BUSINESS_ID/config/config.yaml
   sed -i "s/{{business_id}}/$BUSINESS_ID/g" /home/ubuntu/.hermes/businesses/$BUSINESS_ID/config/config.yaml
   ```
   **Restaurant-specific config additions** (add to `business.restaurant` section):
   ```yaml
   business:
     type: "restaurant"
     owner_whatsapp: "+91XXXXXXXXXX"  # Owner notification number
     restaurant:
       enabled_services:
         - table_booking
         - food_order
         - party_booking
         - normal_chat
       tables: 10
   ```
3. **Prepare session and calendar files**:
   ```bash
   echo "{}" > /home/ubuntu/.hermes/businesses/$BUSINESS_ID/session.json
   echo "{}" > /home/ubuntu/.hermes/businesses/$BUSINESS_ID/config/calendar_credentials.json
   ```
4. **Create PostgreSQL database** (one-time per business):
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE whatsapp_business_$BUSINESS_ID;"
   sudo -u postgres psql -d whatsapp_business_$BUSINESS_ID -c "GRANT ALL ON SCHEMA public TO agency_user;"
   ```
   The `bookings` table is auto-created on first booking confirmation.
5. **Deploy via PM2**:
   ```bash
   pm2 start /home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/daemon.py
            --name whatsapp-$BUSINESS_ID --interpreter python3 -- $BUSINESS_ID
   ```
6. **Save PM2 list** (to survive reboots):
   ```bash
   pm2 save
   ```
7. **Verify deployment**:
   ```bash
   pm2 list | grep whatsapp-$BUSINESS_ID
   pm2 logs whatsapp-$BUSINESS_ID --lines 10
   # Test booking flow:
   cd /home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts
   python3 init.py process $BUSINESS_ID "+919999999999" "I want to book a table" test_001
   # Should return date prompt
   ```

## Phase A: Restaurant Table Booking Flow (Implemented)
**Trigger keywords**: `booking`, `table`, `book` → routes to table_booking flow

**5-step state machine** (stored in `customer_states[sender][context][booking_step]`):
1. **Date** — `Today`, `Tomorrow`, or `DD-MM-YYYY` (validates not in past)
2. **Time slot** — Auto-generated hourly from `working_hours` (e.g., `09:00-10:00`, `10:00-11:00`)
3. **Guests** — Integer (2, 4, 6, 8+)
4. **Customer details** — `Name, +91XXXXXXXXXX` (comma + space separated)
5. **Confirm** — `Confirm`/`Yes`/`Haan`/`Ji` → creates booking

**On confirm**:
- Generates short booking ID (e.g., `2e34bc5a`)
- Inserts into PostgreSQL `bookings` table with `status=confirmed`
- Sends customer confirmation via WhatsApp
- Sends owner notification to `owner_whatsapp` from config
- Schedules 1-hour reminder + no-show check (end_time + 30 min)

**Reminder & No-show system** (runs in background `_reminder_checker_loop` every 60s):
- **1 hour before**: Customer gets reminder with booking details
- **No-show check** (30 min past end time): If status still `confirmed` → updates to `no_show` in memory + PostgreSQL → alerts owner + notifies customer
- Booking statuses: `confirmed`, `seated`, `completed`, `cancelled`, `no_show`

**Test commands**:
```bash
# Syntax check
python3 -c "import ast; ast.parse(open('router.py').read()); print('SYNTAX OK')"
# Keyword coverage
grep -c "table_booking" router.py   # expect 3+
grep -c "booking_step" router.py   # expect 5+
# End-to-end test
python3 init.py process test_biz "+919999999999" "I want to book a table" test_999
```

## Pitfalls
- **Business ID must match**: The `{{business_id}}` placeholder in the config template must be replaced with the actual business ID used in the folder name and PM2 process name. Mismatch causes the agent to look for config in the wrong location.
- **WhatsApp session required**: The agent will not send/receive messages until a valid WhatsApp Web session is present at the path specified in `config.yaml` (`session_file`). Obtain this by scanning the QR code via the central WhatsApp bot (running on port 8080) and saving the session to that path.
- **Calendar credentials**: If calendar integration is enabled, ensure `calendar_credentials.json` contains a valid Google service account key; otherwise booking will fail silently.
- **Database readiness**: The agent assumes a PostgreSQL instance is running with the `agency_user` user and password `secure_password` (as set in the global `.env`). Create the database manually if needed, or the agent will retry until it exists.
- **Rate limits**: WhatsApp outgoing messages are limited to 20/hour by default to avoid being flagged as spam; adjust `rate_limit_per_hour` in config if you have approval for higher limits.
- **Media storage**: Ensure the `media_storage_path` directory exists and is writable; otherwise received images/files will not be saved.
- **Daemon must include a keep-alive loop**: Without a loop that prevents exit, the agent will start and immediately stop, causing repeated restarts. The daemon.py should call `manager.start()` then enter a loop that sleeps indefinitely (e.g., `while True: await asyncio.sleep(3600)`).
- **Webhook port and security group**: The `config.yaml.template` sets `webhook_port` to 8081 to avoid conflicts with AWS security group which only opens ports 22 and 8080 by default. If implementing webhooks, ensure the port is open in the security group.

---
Author: Mohd Zaid (SaaS Builder, Business Operations Focus)
Language: Hinglish-ready responses
Free-tier first: Uses existing Hermes infra (no new paid services)