# Rivox Services - Restaurant Service Flow (v1.1 LOCKED)

## Overview
This document outlines the complete flow for the restaurant service on WhatsApp, covering customer experience, owner configuration, and technical implementation.

## Customer Experience on WhatsApp

### 1. Welcome Message (Triggered on new chat or QR scan)
```
Namaste! 🙏 Welcome to {RESTAURANT NAME}
Service chuniye:
🍽️ 1. Table Booking
🛒 2. Food Order
🎂 3. Party / Birthday Booking
💬 4. Normal Chat
```
- Customers can reply with the number (1-4) or keyword: "booking", "order", "party", "chat"
- Based on enabled services in config, only relevant options are shown

### 2. Table Booking Flow
**Step 1: Date Selection**
- Reply with: "Today", "Tomorrow", or custom date (DD-MM-YYYY)
- System validates and proceeds

**Step 2: Time Slot Selection**
- Available slots auto-generated from owner's working hours (config)
- Format: HH:AM/PM - HH:AM/PM (e.g., 19:00 - 21:00)
- Customer selects one slot

**Step 3: Guest Count**
- Options: 2, 4, 6, 8+ (or custom number)
- System validates against table availability

**Step 4: Customer Details**
- Name (text input)
- Mobile number (with country code, validated)

**Step 5: Confirmation**
- Summary shown: Date, Time, Guests, Name, Mobile
- Customer confirms with "Confirm" or "Yes"

**Post-Confirmation:**
- Customer receives: `Booking #B045 CONFIRMED ✅ (date, time, guests, address)`
- Owner receives WhatsApp notification: `NEW BOOKING #B045 | date time | guests | number`
- System schedules:
  - Reminder 1 hour before booking
  - Auto-cancellation if no-show (15 minutes past booking time)
  - Status tracking: Confirmed → Seated → Completed

### 3. Food Order Flow (Phase B) — IMPLEMENTED
- Welcome menu → `2. Food Order` → categories from `menu.yaml` → item list → quantity (1-10)
- Cart actions: `v` view cart, `cc` clear cart, `0` back to categories, `p` place order
- Order confirmed: `Order Confirmed! #OX…` with subtotal + 5% GST
- Saved to PostgreSQL `orders` table (items JSONB, total, status)
- Owner commands: `status <ORDER_ID> ready|out|delivered` → DB update + customer notified

### 4. Party/Birthday Booking Flow (Phase C) — IMPLEMENTED
- Welcome menu → `3. Party / Birthday Booking` → occasion (Birthday / Anniversary / Custom)
- Date (Today / Tomorrow / DD-MM-YYYY) → package from `party_booking.yaml` (e.g. Silver ₹15,000 / max 30 guests, Gold ₹25,000 / max 50 guests, with time slots)
- Guest count validated against package limit (`0` = back to packages)
- Contact: `name, +91XXXXXXXXXX, email(optional)` → confirmation summary → `Confirm` / `Change`
- Saved to PostgreSQL `party_bookings` table; customer + owner receive WhatsApp notifications

### 5. Normal Chat
- Agent handles generic queries (timings, location, menu) using trained FAQ
- If unrecognized, forwards to owner
- Owner's reply is sent back to customer

## Owner Configuration (Onboarding Form)

### Website Form Fields
- Restaurant Name
- Address
- Owner WhatsApp Number (primary)
- Kitchen/Staff Number(s) (for order notifications)
- Working Hours (start/end, e.g., 11:00 - 23:00)
- Total Tables
- Delivery Radius (km)
- Services Checkbox (enable/disable):
  - [ ] Table Booking
  - [ ] Home Delivery
  - [ ] Takeaway
  - [ ] Dine-in
  - [ ] Party Booking
  - [ ] Online Payment (UPI)
  - [ ] Cash Payment
  - [ ] Feedback Collection
- Language Preference: Hindi / English / Hinglish
- UPI ID (for online payments)
- Menu Upload:
  - Option 1: Upload menu photo (JPG/PNG)
  - Option 2: Upload menu PDF
  - Option 3: Paste menu text
  - System uses FREE Gemini Vision API to extract items, prices, categories
  - Owner receives WhatsApp preview: [Approve] / [Edit]
  - Upon approval, menu goes live

### Editable via Owner WhatsApp (Post-Onboarding)
- Owner can send commands to update:
  - `update menu` -> triggers menu re-upload flow
  - `update hours` -> changes working hours
  - `update upi` -> changes UPI ID
  - `toggle service <service_name>` -> enable/disable a service
  - `view bookings` -> shows today's bookings
  - `view orders` -> shows today's orders

## QR System

### Unique QR Codes
- Each restaurant + table gets a unique QR
- Data encoded: `restaurant_id` + `table_no`
- Short URL format: `https://rivox-services.vercel.app/qr/{biz}/{table}`
- Example: `https://rivox-services.vercel.app/qr/rest123/5`

### Endpoint: `/qr/{biz}/{table}`
- Generates QR image on-the-fly using free Python qrcode library
- When scanned, redirects to welcome message with table number pre-selected for dine-in
- Owner receives printable QR PDF/image via WhatsApp post-onboarding (one per table)

## Technical Implementation

### Reusing Existing Infrastructure
- **WhatsApp Business Agent**: Extend router/intent layer for restaurant intents
- **Config**: `/home/ubuntu/.hermes/businesses/<id>/config.yaml` - add restaurant section
- **Database**: PostgreSQL tables for:
  - `orders` (id, business_id, customer_name, mobile, items, total, status, payment_type, timestamp)
  - `order_items` (id, order_id, item_name, quantity, price)
  - `bookings` (id, business_id, date, time_slot, guests, customer_name, mobile, status, created_at)
  - `menu_items` (id, business_id, name, category, price, is_veg, description)
  - `payments` (id, order_id, upi_transaction_id, status, timestamp)
- **Redis**: Cart/session state (temporary)
- **Scheduler**: 
  - Booking reminders (1 hour before)
  - Party reminders (1 day before)
  - Feedback request (2 hours after service)
  - No-show auto-cancellation (15 minutes past booking time)
- **Bridge API**: 
  - Extend `/onboard` to accept restaurant-specific fields (services[], menu_data, upi, tables)
  - Backward compatible with existing fields
  - New endpoints: `/menu/{biz}`, `/qr/{biz}/{table}`
- **Website**: 
  - `/service/whatsapp` page updated with restaurant setup sections
  - Build order: Phase A (WhatsApp flow) → Phase B (menu/upload + food order) → etc.

## Rules & Constraints
- **No Paid APIs**: Only use free tiers (GROQ/Gemini for menu extraction in Phase B+)
- **RAM Check**: Before spawning new processes, check free RAM (>200MB required)
- **Token Management**: All secrets read from `.env` (never hardcoded)
- **Isolation**: All business data under `/home/ubuntu/.hermes/businesses/<id>/`
- **Documentation**: Save this FLOW.md in repo for reference

## Build Order (Phased)
**Phase A (Current)**: 
- Welcome message with 4 options
- Table Booking flow (full)
- Owner WhatsApp notifications (new bookings)
- Reminders (1 hour before) + no-show cancellation
- Config schema update for restaurant section

**Phase B**: 
- Menu upload/auto-build (using FREE Gemini Vision)
- Food Order flow + cart
- Category-wise item display

**Phase C**: 
- Payment integration (UPI QR/link + cash)
- Order status updates (Confirmed → Preparing → Ready → Out for delivery → Delivered)
- Delivery tracking

**Phase D**: 
- Party/Birthday booking flow
- Feedback/review collection system

**Phase E**: 
- Owner reports/dashboard (daily/weekly sales, booking stats)

## Status Tracking
- After each phase: `pm2 save` + `git push` + status message
- Current status: Phase A in progress
---

# Portal V2 — Glassmorphism Enroll Flow (2026-09-26) ✅ IMPLEMENTED

Home page → service card (glass + neon glow) → detail modal → Enroll → Connect → QR →
Details form → Submit → Lead on AWS → agent starts → test → manual UPI payment → ACTIVE.

## Pages (Vercel — connection path ONLY, no business logic on client)

| Route | What it does |
|---|---|
| `/` | Dark glassmorphism home: hero + 1 service card (**WhatsApp AI Agent**, ₹2,000–5,000/month). Card click → glass detail modal: features + price + `💬 WhatsApp Contact` (wa.me/919899359566) + `⚡ Enroll Now` |
| `/enroll/whatsapp` | 4-step flow (below) |
| `/service/[id]` | Same detail as page (old links keep working) |
| `POST /api/reset-session` | → bridge `/reset-session` → bot logs out + clears auth → fresh QR |
| `GET /api/qr` | → bridge `/qr` → bot QR PNG (existing) |
| `GET /api/verify-phone?phone=` | → bridge `/verify-phone/<digits>` → bot `/whoami` match |
| `POST /api/onboard` | → bridge `/onboard` (full form body pass-through) |
| `GET /api/lead-status/[bid]` | → bridge `/lead-status/<bid>` (payment pending/paid) |

## Enroll steps (frontend/pages/enroll/whatsapp.js)

1. **Connect** — WhatsApp number (auto +91) → `POST /api/reset-session` → fresh QR
2. **Scan QR** — QR image (auto-retry fetch) + 3s polling of verify-phone; auto-advance on match;
   Refresh QR button (re-reset)
3. **Details** (unlocked only after connected) — your name, business name, business type
   (dropdown + Other free-text), address, services/menu, **service pills**
   (Table/Food/Party/FAQ + `Other → type your own` → maps to normal_chat + customNote saved),
   auto Business ID = `slug(name)_<phone last4>`. Submit → bridge `/onboard`
4. **Test & Pay** — success + businessId, test instructions (message from a **second phone** —
   self-chat NOT supported: bot skips `fromMe`), payment card: UPI `rivox@upi` ₹2,000,
   screenshot → wa.me to owner, status pill polls lead-status → `✅ SERVICE ACTIVE` after approve

## Bridge (infra/bridge_api.py, port 8081, pm2 `rivox-bridge`)

- `POST /reset-session` → bot `/reset` (logout, wipe auth_info, fresh QR)
- `GET /verify-phone/<digits>` → bot `/whoami` → entered-vs-connected (last-10 fallback)
- `POST /onboard` (extended) → business dir + template config + **config injection**
  (name, type, owner_whatsapp, enabled_services from form, generic 3-QA FAQ with address),
  **lead file** `.hermes/leads/<bid>.json` (payment: pending), **phone map**
  `.hermes/phone_map.json` (`+number → businessId`), **per-business PG DB**
  `whatsapp_business_<bid>` (CREATE DATABASE + `infra/schema.sql`), pm2 agent start
  (`whatsapp-<bid>`), returns `{success, businessId}`
- `GET /lead-status/<bid>` / `POST /approve/<bid>` (token) → payment paid + status active
- Auth: `X-API-Key` = Vercel env `ONBOARD_API_TOKEN` (= `mysecrettoken123`, matches bridge pm2 env)

## Bot (whatsapp-bot/index.js, port 8080)

- `POST /reset` — logout + clear auth → fresh QR (generation counter prevents double sockets)
- `GET /whoami` — `{connected, number: "+91..."}`
- **Dynamic businessId**: connected number → phone_map lookup → `test_biz` fallback
- `connection.open` → writes `.hermes/businesses/<bid>/session.json` marker (if mapped)
- `ROUTER_API_KEY` pm2 env = `rivox-router-...` (router 8082 requires it — was MISSING, fixed)

## Limits / Rules

- **Single WhatsApp session at a time** — each new enroll resets the previous QR session
- Self-chat testing not supported (fromMe skipped) — test from another number
- Payment = manual UPI + screenshot → owner/Hermes approves:
  `curl -X POST -H 'X-API-Key: <bridge token>' http://127.0.0.1:8081/approve/<businessId>`
- `.hermes/leads/*.json` = source of truth for new enrollments (Hermes watches this)
- Portal stays on Vercel (connection path only); leads/agents/DB stay in `.hermes/` on EC2

## Phase 2 (pending — Hermes)

- Auto-fill agent: site ↔ Hermes ↔ owner WhatsApp (agent pre-fills customer details)
- Lead finding + outreach agent on WhatsApp (fast customer acquisition)
