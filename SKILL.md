---
name: whatsapp-business-agent
description: Provides WhatsApp automation for local businesses.
category: autonomous-ai-agents
---

# WhatsApp Business Agent - Complete Automation for Local Businesses

## Description
Use when deploying WhatsApp automation for local businesses (restaurants, salons, clinics). Provides auto-reply, booking management, reminders, follow-ups, and review collection via personal WhatsApp Web (Baileys). Each business gets isolated deployment with strong connection to central Hermes infrastructure.

## Core Features
- Auto-reply Agent: Instant responses to customer messages using intent detection
- Booking Manager: Calendar integration for appointments (Google Calendar/Simple DB)
- Reminder System: Automated SMS/WhatsApp reminders before appointments
- Follow-up Agent: Post-service check-ins and review requests
- Review Collector: Automates feedback collection and public review posting
- Business Isolation: Separate DB schemas/config per business; shared agent code
- Hermes Integration: Uses Redis (scheduler), PostgreSQL (data), Monitor Agent (health checks)

## Deployment
1. Create business config: mkdir -p /home/ubuntu/.hermes/businesses/<business_name>/config
2. Copy template config: cp /home/ubuntu/.hermes/skills/whatsapp-business-agent/config.yaml.template /home/ubuntu/.hermes/businesses/<business_name>/config/config.yaml
3. Edit config with business-specific DB schema, WhatsApp number, etc.
4. Deploy instance: pm2 start /home/ubuntu/.hermes/skills/whatsapp-business-agent/scripts/daemon.py --name whatsapp-<business_name> --interpreter python3 -- <business_name>
5. Monitor via central monitor-agent (tags: business:<business_name>)

## Prerequisites
- WhatsApp number linked via Baileys QR scan (done once per business)
- Central Hermes services running: Redis, PostgreSQL, monitor-agent
- Business Google Calendar API key (optional for booking)

## Output
- 24/7 WhatsApp automation per business
- Monthly recurring revenue model (Rs. 2000-5000/business)
- Zero manual intervention after setup

---
Author: Mohd Zaid (SaaS Builder, Business Operations Focus)
Language: Hinglish-ready responses
Free-tier first: Uses existing Hermes infra (no new paid services)
