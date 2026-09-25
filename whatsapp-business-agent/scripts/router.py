"""WhatsApp Business Agent Router
Handles routing of messages and business logic for WhatsApp automation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class Router:
    def __init__(self, provider_registry):
        self.provider_registry = provider_registry
        self.background_tasks = []
        self.stats = {
            "messages_processed": 0,
            "appointments_scheduled": 0,
            "reminders_sent": 0,
            "reviews_requested": 0,
            "auto_replies_sent": 0,
            "follow_ups_sent": 0,
            "restaurant_welcome_sent": 0,
            "restaurant_bookings_created": 0,
        }
        # In-memory storage for simplicity (in production, use database)
        self.pending_reminders = []  # List of reminders to send
        self.appointments = {}       # appointment_id -> appointment details
        self.customer_states = {}    # customer_id -> state for conversation flow
        self.restaurant_bookings = {}  # booking_id -> booking details

    async def start_background_tasks(self):
        """Start background tasks like reminder checker."""
        # Task to check for pending reminders every minute
        reminder_task = asyncio.create_task(self._reminder_checker_loop())
        self.background_tasks.append(reminder_task)
        logger.info("Background tasks started")

    async def stop_background_tasks(self):
        """Stop all background tasks."""
        for task in self.background_tasks:
            task.cancel()
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
        logger.info("Background tasks stopped")

    async def _reminder_checker_loop(self):
        """Check every minute for reminders that need to be sent."""
        while True:
            try:
                await self._process_pending_reminders()
            except Exception as e:
                logger.error(f"Error in reminder checker: {e}")
            await asyncio.sleep(60)  # Check every minute

    async def _process_pending_reminders(self):
        """Send reminders that are due."""
        now = datetime.now()
        to_remove = []
        for i, reminder in enumerate(self.pending_reminders):
            if reminder["send_at"] <= now:
                reminder_type = reminder.get("reminder_type")
                if reminder_type == "no_show_check":
                    # Handle no-show check for restaurant bookings
                    success = await self._handle_no_show_check(reminder)
                elif reminder_type in ("1h_before", "24h"):
                    # Handle restaurant booking reminders
                    success = await self._send_restaurant_booking_reminder(
                        reminder["booking_id"],
                        reminder["reminder_type"],
                        reminder["customer_phone"]
                    )
                else:
                    # Handle generic appointment reminders
                    success = await self._send_reminder(
                        reminder["appointment_id"],
                        reminder["reminder_type"],
                        reminder["customer_phone"]
                    )
                if success:
                    logger.info(f"Sent reminder {reminder['reminder_type']} for booking {reminder.get('booking_id', reminder.get('appointment_id'))}")
                else:
                    logger.error(f"Failed to send reminder for booking {reminder.get('booking_id', reminder.get('appointment_id'))}")
                to_remove.append(i)

        # Remove processed reminders (in reverse order to not mess up indices)
        for i in reversed(to_remove):
            self.pending_reminders.pop(i)

    def get_stats(self) -> dict:
        """Return a copy of current statistics."""
        return dict(self.stats)

    async def handle_incoming_message(self, sender: str, message: str, message_id: str) -> Dict[str, Any]:
        """Process incoming WhatsApp message and return response."""
        self.stats["messages_processed"] += 1
        logger.info(f"Processing message from {sender}: {message}")

        # Get or create customer state
        if sender not in self.customer_states:
            self.customer_states[sender] = {
                "state": "greeting",
                "context": {},
                "last_interaction": datetime.now(),
                "flow_type": None  # 'generic' or 'restaurant'
            }
        state = self.customer_states[sender]
        state["last_interaction"] = datetime.now()

        # Normalize message
        message_lower = message.lower().strip()

        # Determine business type from config
        business_type = self.provider_registry.config.get('business', {}).get('type', 'general')

        # Route based on business type and current state
        if business_type == 'restaurant':
            return await self._handle_restaurant_message(sender, message, state, message_lower)
        else:
            return await self._handle_generic_message(sender, message, state, message_lower)

    # ------------------- Generic Handlers (Unchanged) -------------------
    async def _handle_generic_message(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle messages for generic business type (original logic)."""
        # Get or create customer state
        if sender not in self.customer_states:
            self.customer_states[sender] = {
                "state": "greeting",
                "context": {},
                "last_interaction": datetime.now()
            }
        state = self.customer_states[sender]
        state["last_interaction"] = datetime.now()

        # Normalize message
        message_lower = message.lower().strip()

        # Check for common commands/intents
        if any(greeting in message_lower for greeting in ["hi", "hello", "hey", "namaste", "namaskar"]):
            return await self._handle_greeting(sender, message, state)
        elif any(word in message_lower for word in ["book", "appointment", "schedule", "meet"]):
            return await self._handle_booking_request(sender, message, state)
        elif any(word in message_lower for word in ["cancel", "reschedule", "change"]):
            return await self._handle_cancel_reschedule(sender, message, state)
        elif any(word in message_lower for word in ["confirm", "yes", "haan", "ji"]):
            return await self._handle_confirmation(sender, message, state)
        elif any(word in message_lower for word in ["no", "nahi", "cancel"]):
            return await self._handle_negative(sender, message, state)
        elif any(word in message_lower for word in ["review", "feedback", "rating"]):
            return await self._handle_review_request(sender, message, state)
        else:
            # Default to auto-reply from templates
            return await self._send_auto_reply(sender, message, state)

    async def _handle_greeting(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle greeting messages."""
        state["state"] = "greeting"
        template = self.provider_registry.config["templates"]["auto_reply"]["greeting"]
        business_name = self.provider_registry.config["business"]["name"] or "our business"
        reply = template.format(business_name=business_name)
        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "auto_reply",
            "state": state["state"]
        }

    async def _handle_booking_request(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle appointment booking request."""
        state["state"] = "booking"
        # Extract details from message (simplified)
        # In reality, we would use NLP to extract date, time, service type
        reply = self.provider_registry.config["templates"]["auto_reply"]["booking_confirm"]
        business_name = self.provider_registry.config["business"]["name"] or "our business"
        # For now, we'll ask for details
        reply = f"Great! I'd like to book an appointment for you at {business_name}. " \
                "Please tell me:\n1. What service do you need?\n2. Preferred date?\n3. Preferred time?"
        state["context"]["booking_step"] = "service"
        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "booking_request",
            "state": state["state"]
        }

    async def _handle_cancel_reschedule(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle cancellation or rescheduling request."""
        state["state"] = "modify_booking"
        reply = "I can help you cancel or reschedule your appointment. " \
                "Please provide your appointment ID or the date/time of your appointment."
        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "modify_booking",
            "state": state["state"]
        }

    async def _handle_confirmation(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle confirmation messages."""
        if state["state"] == "booking":
            # We have collected booking details, now schedule
            # For simplicity, we'll create a dummy appointment
            appointment_id = f"apt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            start_time = datetime.now() + timedelta(days=1)  # Tomorrow
            end_time = start_time + timedelta(minutes=30)

            # Schedule in calendar
            attendee_info = {
                "email": None,  # We don't have email from WhatsApp easily
                "phone": sender
            }
            success = await self.schedule_appointment(
                f"Appointment with {self.provider_registry.config['business']['name'] or 'Business'}",
                f"Service discussed via WhatsApp",
                start_time,
                end_time,
                attendee_info
            )

            if success:
                self.appointments[appointment_id] = {
                    "customer_phone": sender,
                    "start_time": start_time,
                    "end_time": end_time,
                    "status": "confirmed"
                }
                self.stats["appointments_scheduled"] += 1

                # Schedule reminders
                await self._schedule_reminders_for_appointment(appointment_id, sender)

                reply = self.provider_registry.config["templates"]["auto_reply"]["booking_confirm"] \
                    .format(date=start_time.strftime("%B %d, %Y"), time=start_time.strftime("%I:%M %p"))
                state["state"] = "confirmed"
                state["context"]["appointment_id"] = appointment_id
            else:
                reply = "Sorry, I couldn't schedule your appointment at this time. Please try again later."
                state["state"] = "error"

            self.stats["auto_replies_sent"] += 1
            return {
                "response": reply,
                "action": "booking_confirmed" if success else "booking_failed",
                "state": state["state"]
            }
        else:
            # Generic confirmation
            reply = "Thank you for confirming! Is there anything else I can help you with?"
            self.stats["auto_replies_sent"] += 1
            return {
                "response": reply,
                "action": "generic_confirmation",
                "state": state["state"]
            }

    async def _handle_negative(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle negative responses."""
        reply = "No problem! Let me know if you change your mind or need help with something else."
        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "negative_response",
            "state": state["state"]
        }

    async def _handle_review_request(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Handle review requests."""
        state["state"] = "review"
        # We would typically ask for a review after a service
        reply = self.provider_registry.config["templates"]["auto_reply"]["review_request"] \
            .format(review_link="https://example.com/review")  # Placeholder
        self.stats["reviews_requested"] += 1
        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "review_requested",
            "state": state["state"]
        }

    async def _send_auto_reply(self, sender: str, message: str, state: dict) -> Dict[str, Any]:
        """Send a default auto-reply based on current state or greeting."""
        # If we are in the middle of a booking flow, guide them
        if state["state"] == "booking":
            return await self._handle_booking_request(sender, message, state)
        elif state["state"] == "modify_booking":
            return await self._handle_cancel_reschedule(sender, message, state)
        else:
            # Default to greeting
            return await self._handle_greeting(sender, message, state)

    async def schedule_appointment(self, title: str, description: str, start_time: datetime,
                                 end_time: datetime, attendee_info: Dict[str, Any]) -> bool:
        """Schedule appointment via calendar integration."""
        try:
            success = self.provider_registry.schedule_calendar_event(
                title, description, start_time, end_time,
                attendee_info.get("email") if attendee_info else None
            )
            if success:
                logger.info(f"Scheduled appointment: {title} from {start_time} to {end_time}")
            return success
        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            return False

    async def send_reminder(self, appointment_id: str, reminder_type: str, customer_phone: str) -> bool:
        """Send reminder for an appointment."""
        try:
            appointment = self.appointments.get(appointment_id)
            if not appointment:
                logger.error(f"Appointment {appointment_id} not found")
                return False

            template = self.provider_registry.config["templates"]["auto_reply"]["reminder"]
            # Format time
            time_str = appointment["start_time"].strftime("%I:%M %p")
            reply = template.format(time=time_str)

            # Send via WhatsApp
            success = self.provider_registry.send_whatsapp_message(customer_phone, reply)
            if success:
                self.stats["reminders_sent"] += 1
                logger.info(f"Sent {reminder_type} reminder to {customer_phone} for appointment {appointment_id}")
            return success
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False

    async def request_review(self, customer_id: str, service_details: Dict[str, Any]) -> bool:
        """Request review from customer after service."""
        try:
            # In a real system, we would get the customer's phone from service_details or database
            customer_phone = service_details.get("phone")
            if not customer_phone:
                logger.error("No phone number for review request")
                return False

            template = self.provider_registry.config["templates"]["auto_reply"]["review_request"]
            review_link = service_details.get("review_link", "https://example.com/review")
            reply = template.format(review_link=review_link)

            success = self.provider_registry.send_whatsapp_message(customer_phone, reply)
            if success:
                self.stats["reviews_requested"] += 1
                logger.info(f"Sent review request to {customer_phone}")
            return success
        except Exception as e:
            logger.error(f"Error requesting review: {e}")
            return False

    async def _schedule_reminders_for_appointment(self, appointment_id: str, customer_phone: str):
        """Schedule reminders for an appointment (e.g., 24 hours and 1 hour before)."""
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return

        start_time = appointment["start_time"]

        # 24 hours before
        reminder_24h = start_time - timedelta(hours=24)
        if reminder_24h > datetime.now():
            self.pending_reminders.append({
                "appointment_id": appointment_id,
                "reminder_type": "24h",
                "customer_phone": customer_phone,
                "send_at": reminder_24h
            })

        # 1 hour before
        reminder_1h = start_time - timedelta(hours=1)
        if reminder_1h > datetime.now():
            self.pending_reminders.append({
                "appointment_id": appointment_id,
                "reminder_type": "1h",
                "customer_phone": customer_phone,
                "send_at": reminder_1h
            })

    async def _send_restaurant_booking_reminder(self, booking_id: str, reminder_type: str, customer_phone: str) -> bool:
        """Send reminder for a restaurant booking (1 hour before)."""
        try:
            booking = self.restaurant_bookings.get(booking_id)
            if not booking:
                logger.error(f"Booking {booking_id} not found for reminder")
                return False

            date = booking.get("date")
            time_slot = booking.get("time_slot")
            guests = booking.get("guests")
            customer_name = booking.get("customer_name")
            customer_mobile = booking.get("customer_mobile")

            if not date or not time_slot:
                logger.error(f"Booking {booking_id} missing date or time slot")
                return False

            date_str = date.strftime("%d-%m-%Y")
            time_str = f"{time_slot[0].strftime('%I:%M %p')} - {time_slot[1].strftime('%I:%M %p')}"

            reminder_msg = f"⏰ Reminder: Your table booking #{booking_id} is in 1 hour!\nDate: {date_str}\nTime: {time_str}\nGuests: {guests}\nName: {customer_name}\nMobile: {customer_mobile}\n\nPlease arrive on time. Reply 'CANCEL' if you need to cancel."

            success = self.provider_registry.send_whatsapp_message(customer_phone, reminder_msg)
            if success:
                self.stats["reminders_sent"] += 1
                logger.info(f"Sent {reminder_type} reminder to {customer_phone} for booking {booking_id}")
            return success
        except Exception as e:
            logger.error(f"Error sending restaurant booking reminder: {e}")
            return False

    async def _handle_no_show_check(self, reminder: dict) -> bool:
        """Handle no-show check: if booking is still confirmed 30 min after end time, cancel and notify owner."""
        try:
            booking_id = reminder.get("booking_id")
            booking = self.restaurant_bookings.get(booking_id)
            if not booking:
                logger.error(f"Booking {booking_id} not found for no-show check")
                return False

            # Check if booking is still confirmed
            if booking.get("status") != "confirmed":
                logger.info(f"Booking {booking_id} already updated to {booking.get('status')}, skipping no-show check")
                return True

            # Check in PostgreSQL as well
            try:
                conn = self.provider_registry.get_database_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT status FROM bookings WHERE id = %s", (booking_id,))
                    row = cursor.fetchone()
                    conn.close()
                    if row and row[0] != "confirmed":
                        logger.info(f"Booking {booking_id} in DB already updated to {row[0]}, skipping no-show check")
                        return True
            except Exception as e:
                logger.error(f"Error checking booking status in DB: {e}")

            # Still confirmed - cancel it
            booking["status"] = "no_show"

            # Update in PostgreSQL
            try:
                conn = self.provider_registry.get_database_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE bookings SET status = 'no_show' WHERE id = %s", (booking_id,))
                    conn.commit()
                    conn.close()
            except Exception as e:
                logger.error(f"Error updating booking status in DB: {e}")

            # Notify owner
            owner_whatsapp = self.provider_registry.config.get('business', {}).get('owner_whatsapp', '')
            if owner_whatsapp:
                date = booking.get("date")
                time_slot = booking.get("time_slot")
                guests = booking.get("guests")
                customer_mobile = booking.get("customer_mobile")
                date_str = date.strftime("%d-%m-%Y") if date else "Unknown"
                time_str = f"{time_slot[0].strftime('%I:%M %p')} - {time_slot[1].strftime('%I:%M %p')}" if time_slot else "Unknown"
                owner_msg = f"⚠️ NO-SHOW: Booking #{booking_id} | {date_str} {time_str} | {guests} guests | {customer_mobile} | Customer did not arrive"
                try:
                    self.provider_registry.send_whatsapp_message(owner_whatsapp, owner_msg)
                    logger.info(f"Sent no-show alert to owner: {owner_whatsapp}")
                except Exception as e:
                    logger.error(f"Failed to send no-show alert to owner: {e}")

            # Notify customer
            customer_phone = booking.get("customer_phone")
            if customer_phone:
                customer_msg = f"❌ Your booking #{booking_id} has been marked as NO-SHOW and cancelled.\nWe missed you! Please contact us to rebook."
                try:
                    self.provider_registry.send_whatsapp_message(customer_phone, customer_msg)
                except Exception as e:
                    logger.error(f"Failed to send no-show notification to customer: {e}")

            logger.info(f"Booking {booking_id} marked as no-show and notifications sent")
            return True
        except Exception as e:
            logger.error(f"Error in no-show check: {e}")
            return False

    # ------------------- Restaurant Specific Handlers -------------------
    async def _handle_restaurant_message(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle messages for restaurant business type."""
        flow_type = state.get("flow_type")

        # Stage 0: first message — keyword shortcut or welcome menu
        if state["state"] == "greeting" and flow_type is None:
            choice = self._match_service_choice(message_lower)
            if choice in ("table_booking", "food_order", "party_booking"):
                return await self._start_service_flow(choice, sender, state)
            return await self._restaurant_welcome(sender, state)

        # Stage 1: welcome menu shown — parse the service choice
        if state["state"] == "awaiting_service_choice" and flow_type is None:
            choice = self._match_service_choice(message_lower)
            if choice:
                return await self._start_service_flow(choice, sender, state)
            return await self._restaurant_welcome(sender, state)

        # Stage 2: inside a chosen service flow
        if flow_type == "table_booking":
            return await self._handle_restaurant_table_booking(sender, message, state, message_lower)
        elif flow_type == "food_order":
            # Placeholder for food order flow (to be implemented in Phase B)
            return await self._restaurant_default_reply(sender, state, "Food order flow coming soon!")
        elif flow_type == "party_booking":
            # Placeholder for party booking flow (to be implemented in Phase C)
            return await self._restaurant_default_reply(sender, state, "Party booking flow coming soon!")
        elif flow_type == "normal_chat":
            return await self._handle_restaurant_normal_chat(sender, message, state, message_lower)
        else:
            # Default to welcome if flow_type is not set
            return await self._restaurant_welcome(sender, state)

    def _match_service_choice(self, message_lower: str):
        """Map menu numbers or free text to a service id (or None)."""
        msg = message_lower.strip().lower().strip(".! ")
        if not msg:
            return None
        if msg == "1" or "table" in msg or "booking" in msg or msg == "book":
            return "table_booking"
        if msg == "2" or "food" in msg or "order" in msg or "menu" in msg:
            return "food_order"
        if msg == "3" or "party" in msg or "birthday" in msg or "anniversary" in msg:
            return "party_booking"
        if msg == "4" or msg == "chat" or msg == "normal chat":
            return "normal_chat"
        return None

    async def _start_service_flow(self, choice: str, sender: str, state: dict) -> Dict[str, Any]:
        """Set flow_type and send the first prompt of the chosen service."""
        state["flow_type"] = choice
        if choice == "table_booking":
            booking_context = state.get("context", {})
            booking_context["booking_step"] = "date"
            state["context"] = booking_context
            state["state"] = "restaurant_booking"
            return {
                "response": "Booking ke liye date chuniye: 'Today', 'Tomorrow' ya DD-MM-YYYY (e.g. 28-09-2026).",
                "action": "booking_date_prompt",
                "state": state["state"],
            }
        if choice == "food_order":
            return await self._restaurant_default_reply(sender, state, "Food order flow coming soon!")
        if choice == "party_booking":
            return await self._restaurant_default_reply(sender, state, "Party booking flow coming soon!")
        # normal_chat
        return await self._restaurant_default_reply(
            sender, state,
            "Theek hai — normal chat! Timings, location, menu — kuch bhi puchiye."
        )

    async def _restaurant_welcome(self, sender: str, state: dict) -> Dict[str, Any]:
        """Send the restaurant welcome message with 4 options."""
        business_name = self.provider_registry.config.get('business', {}).get('name', 'our restaurant')
        # Get enabled services from config
        enabled_services = self.provider_registry.config.get('business', {}).get('restaurant', {}).get('enabled_services', [])
        service_map = {
            'table_booking': '🍽️ 1. Table Booking',
            'food_order': '🛒 2. Food Order',
            'party_booking': '🎂 3. Party / Birthday Booking',
            'normal_chat': '💬 4. Normal Chat'
        }
        service_lines = []
        for svc in enabled_services:
            if svc in service_map:
                service_lines.append(service_map[svc])
        services_str = '\n'.join(service_lines) if service_lines else 'No services enabled'
        welcome_msg = f"Namaste! 🙏 Welcome to {business_name}\n\nService chuniye:\n{services_str}"
        state["state"] = "awaiting_service_choice"
        self.stats["restaurant_welcome_sent"] += 1
        return {
            "response": welcome_msg,
            "action": "restaurant_welcome",
            "state": state["state"]
        }

    async def _handle_restaurant_table_booking(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle the table booking flow for restaurant."""
        booking_context = state.get("context", {})
        step = booking_context.get("booking_step")

        if step == "date":
            return await self._restaurant_booking_date(sender, message, state, message_lower)
        elif step == "time_slot":
            return await self._restaurant_booking_time_slot(sender, message, state, message_lower)
        elif step == "guests":
            return await self._restaurant_booking_guests(sender, message, state, message_lower)
        elif step == "customer_details":
            return await self._restaurant_booking_customer_details(sender, message, state, message_lower)
        elif step == "confirm":
            return await self._restaurant_booking_confirm(sender, message, state, message_lower)
        else:
            # Default to asking for date
            booking_context["booking_step"] = "date"
            state["context"] = booking_context
            return await self._restaurant_booking_date(sender, message, state, message_lower)

    async def _restaurant_booking_date(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle date selection for table booking."""
        # Parse date: today, tomorrow, or custom (DD-MM-YYYY)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        booking_date = None

        if message_lower in ["today", "aaj"]:
            booking_date = today
        elif message_lower in ["tomorrow", "kal"]:
            booking_date = tomorrow
        else:
            # Try to parse DD-MM-YYYY
            try:
                day, month, year = map(int, message_lower.split('-'))
                booking_date = datetime(year, month, day)
                # Validate that the date is not in the past
                if booking_date.date() < today.date():
                    return {
                        "response": "Date cannot be in the past. Please enter a valid date (DD-MM-YYYY) or say 'Today' or 'Tomorrow'.",
                        "action": "invalid_date",
                        "state": state["state"]
                    }
            except:
                return {
                    "response": "Please enter a valid date in DD-MM-YYYY format, or say 'Today' or 'Tomorrow'.",
                    "action": "invalid_date",
                    "state": state["state"]
                }

        # Store the date and move to time slot selection
        booking_context = state.get("context", {})
        booking_context["date"] = booking_date
        booking_context["booking_step"] = "time_slot"
        state["context"] = booking_context

        # Generate time slots from working hours
        working_hours = self.provider_registry.config.get('business', {}).get('working_hours', {})
        start_str = working_hours.get('start', "09:00")
        end_str = working_hours.get('end', "18:00")
        try:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
        except:
            start_time = datetime.strptime("09:00", "%H:%M").time()
            end_time = datetime.strptime("18:00", "%H:%M").time()

        # Generate slots of 1 hour each
        slots = []
        current = datetime.combine(booking_date.date(), start_time)
        end_datetime = datetime.combine(booking_date.date(), end_time)
        while current < end_datetime:
            slot_end = current + timedelta(hours=1)
            slots.append((current.time(), slot_end.time()))
            current = slot_end

        if not slots:
            return {
                "response": "No time slots available for the selected date. Please choose another date.",
                "action": "no_slots",
                "state": state["state"]
            }

        # Format slots for display
        slots_msg = "Available time slots:\n"
        for i, (start, end) in enumerate(slots, 1):
            slots_msg += f"{i}. {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}\n"
        slots_msg += "\nPlease reply with the slot number (e.g., 1) or time range (e.g., '19:00 - 21:00')."

        return {
            "response": slots_msg,
            "action": "time_slot_selection",
            "state": state["state"]
        }

    async def _restaurant_booking_time_slot(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle time slot selection for table booking."""
        booking_context = state.get("context", {})
        booking_date = booking_context.get("date")
        if not booking_date:
            return await self._restaurant_welcome(sender, state)  # Reset if date missing

        # Parse the time slot from message
        # Try to parse as a number (slot index) or as a time range
        selected_slot = None
        try:
            slot_index = int(message_lower) - 1
            working_hours = self.provider_registry.config.get('business', {}).get('working_hours', {})
            start_str = working_hours.get('start', "09:00")
            end_str = working_hours.get('end', "18:00")
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
            slots = []
            current = datetime.combine(booking_date.date(), start_time)
            end_datetime = datetime.combine(booking_date.date(), end_time)
            while current < end_datetime:
                slot_end = current + timedelta(hours=1)
                slots.append((current.time(), slot_end.time()))
                current = slot_end
            if 0 <= slot_index < len(slots):
                selected_slot = slots[slot_index]
        except:
            # Try to parse as time range HH:MM - HH:MM
            try:
                if '-' in message_lower:
                    start_str, end_str = message_lower.split('-')
                    start_str = start_str.strip()
                    end_str = end_str.strip()
                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    end_time = datetime.strptime(end_str, "%H:%M").time()
                    selected_slot = (start_time, end_time)
            except:
                pass

        if not selected_slot:
            return {
                "response": "Please select a valid time slot by number or time range (e.g., '19:00 - 21:00').",
                "action": "invalid_time_slot",
                "state": state["state"]
            }

        # Store the selected time slot and move to guest count
        booking_context["time_slot"] = selected_slot
        booking_context["booking_step"] = "guests"
        state["context"] = booking_context

        return {
            "response": "How many guests? Please reply with the number (2, 4, 6, 8+).",
            "action": "guest_count_selection",
            "state": state["state"]
        }

    async def _restaurant_booking_guests(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle guest count selection for table booking."""
        try:
            guests = int(message_lower)
            if guests <= 0:
                raise ValueError
        except:
            return {
                "response": "Please enter a valid number of guests (e.g., 2, 4, 6, 8).",
                "action": "invalid_guests",
                "state": state["state"]
            }

        # Store guest count and move to customer details
        booking_context = state.get("context", {})
        booking_context["guests"] = guests
        booking_context["booking_step"] = "customer_details"
        state["context"] = booking_context

        return {
            "response": "Please provide your name and mobile number (with country code) separated by a comma.\nExample: 'John Doe, +919876543210'",
            "action": "customer_details_input",
            "state": state["state"]
        }

    async def _restaurant_booking_customer_details(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle customer details input for table booking."""
        # Parse name and mobile
        if ', ' not in message_lower:
            return {
                "response": "Please provide both name and mobile number separated by a comma and a space.\nExample: 'John Doe, +919876543210'",
                "action": "invalid_customer_details",
                "state": state["state"]
            }

        parts = message_lower.split(', ', 1)
        name = parts[0].strip()
        mobile = parts[1].strip()

        # Basic mobile validation (should start with + and have digits)
        if not mobile.startswith('+') or not mobile[1:].isdigit():
            return {
                "response": "Mobile number must start with '+' followed by digits (e.g., +919876543210).",
                "action": "invalid_mobile",
                "state": state["state"]
            }

        if not name:
            return {
                "response": "Name cannot be empty.",
                "action": "invalid_name",
                "state": state["state"]
            }

        # Store customer details and move to confirmation
        booking_context = state.get("context", {})
        booking_context["customer_name"] = name
        booking_context["customer_mobile"] = mobile
        booking_context["booking_step"] = "confirm"
        state["context"] = booking_context

        # Prepare confirmation message
        date = booking_context.get("date")
        time_slot = booking_context.get("time_slot")
        guests = booking_context.get("guests")
        customer_name = booking_context.get("customer_name")
        customer_mobile = booking_context.get("customer_mobile")

        date_str = date.strftime("%d-%m-%Y") if date else "Unknown"
        time_str = f"{time_slot[0].strftime('%I:%M %p')} - {time_slot[1].strftime('%I:%M %p')}" if time_slot else "Unknown"

        confirm_msg = f"Please confirm your booking:\n\nDate: {date_str}\nTime: {time_str}\nGuests: {guests}\nName: {customer_name}\nMobile: {customer_mobile}\n\nReply 'Confirm' to book or 'Change' to modify."

        return {
            "response": confirm_msg,
            "action": "booking_confirmation",
            "state": state["state"]
        }

    async def _restaurant_booking_confirm(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle booking confirmation and create the booking."""
        if message_lower not in ["confirm", "yes", "haan", "ji"]:
            if message_lower in ["change", "modify"]:
                # Go back to date selection
                booking_context = state.get("context", {})
                booking_context["booking_step"] = "date"
                state["context"] = booking_context
                return await self._restaurant_booking_date(sender, message, state, message_lower)
            else:
                return {
                    "response": "Please reply 'Confirm' to book or 'Change' to modify your booking.",
                    "action": "invalid_confirmation",
                    "state": state["state"]
                }

        # All details are present, create the booking
        booking_context = state.get("context", {})
        date = booking_context.get("date")
        time_slot = booking_context.get("time_slot")
        guests = booking_context.get("guests")
        customer_name = booking_context.get("customer_name")
        customer_mobile = booking_context.get("customer_mobile")

        # Generate a booking ID
        booking_id = str(uuid.uuid4())[:8]  # Short ID for simplicity

        # Store the booking in PostgreSQL
        try:
            conn = self.provider_registry.get_database_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bookings (id, customer_phone, customer_name, customer_mobile, booking_date, time_start, time_end, guests, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    booking_id,
                    sender,
                    customer_name,
                    customer_mobile,
                    date.date(),
                    time_slot[0],
                    time_slot[1],
                    guests,
                    "confirmed",
                    datetime.now()
                ))
                conn.commit()
                conn.close()
                logger.info(f"Booking {booking_id} inserted into PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to insert booking into PostgreSQL: {e}")

        # Store the booking in memory (for quick access)
        self.restaurant_bookings[booking_id] = {
            "customer_phone": sender,
            "customer_name": customer_name,
            "customer_mobile": customer_mobile,
            "date": date,
            "time_slot": time_slot,
            "guests": guests,
            "status": "confirmed",
            "created_at": datetime.now()
        }

        # Update stats
        self.stats["restaurant_bookings_created"] += 1

        # Send confirmation to customer
        date_str = date.strftime("%d-%m-%Y")
        time_str = f"{time_slot[0].strftime('%I:%M %p')} - {time_slot[1].strftime('%I:%M %p')}"
        customer_confirm = f"Booking #{booking_id} CONFIRMED ✅\nDate: {date_str}\nTime: {time_str}\nGuests: {guests}\nName: {customer_name}\nMobile: {customer_mobile}"

        # Send notification to owner
        owner_whatsapp = self.provider_registry.config.get('business', {}).get('owner_whatsapp', '')
        if owner_whatsapp:
            owner_msg = f"NEW BOOKING #{booking_id} | {date_str} {time_str} | {guests} guests | {customer_mobile}"
            try:
                self.provider_registry.send_whatsapp_message(owner_whatsapp, owner_msg)
                logger.info(f"Sent booking notification to owner: {owner_whatsapp}")
            except Exception as e:
                logger.error(f"Failed to send booking notification to owner: {e}")

        # Schedule reminders
        # Combine date and time slot to get start datetime
        start_time = datetime.combine(date.date(), time_slot[0])
        end_time = datetime.combine(date.date(), time_slot[1])

        # Reminder 1 hour before
        reminder_time = start_time - timedelta(hours=1)
        if reminder_time > datetime.now():
            self.pending_reminders.append({
                "booking_id": booking_id,
                "reminder_type": "1h_before",
                "customer_phone": sender,
                "send_at": reminder_time
            })

        # No-show cancellation: 30 minutes past the end time (as per requirement)
        # We will check for no-shows in the reminder checker by checking if the booking is still confirmed and current time > end_time + 30min
        # For simplicity, we will add a special reminder type for no-show check.
        no_show_check_time = end_time + timedelta(minutes=30)
        if no_show_check_time > datetime.now():
            self.pending_reminders.append({
                "booking_id": booking_id,
                "reminder_type": "no_show_check",
                "customer_phone": sender,  # We will use this to check and cancel if needed
                "send_at": no_show_check_time
            })

        # Reset the customer state for this flow
        state["state"] = "greeting"
        state["context"] = {}
        state["flow_type"] = None

        return {
            "response": customer_confirm,
            "action": "restaurant_booking_confirmed",
            "state": state["state"]
        }

    async def _handle_restaurant_normal_chat(self, sender: str, message: str, state: dict, message_lower: str) -> Dict[str, Any]:
        """Handle normal chat for restaurant (FAQ-like)."""
        # For now, we will use a simple keyword-based response.
        # In a real system, we would use a trained model or a knowledge base.
        business_name = self.provider_registry.config.get('business', {}).get('name', 'our restaurant')
        working_hours = self.provider_registry.config.get('business', {}).get('working_hours', {})
        start = working_hours.get('start', "09:00")
        end = working_hours.get('end', "18:00")

        if any(word in message_lower for word in ["hour", "time", "open", "close"]):
            reply = f"We are open from {start} to {end} daily."
        elif any(word in message_lower for word in ["location", "address", "where"]):
            address = self.provider_registry.config.get('business', {}).get('address', "Address not configured")
            reply = f"Our address is: {address}"
        elif any(word in message_lower for word in ["menu", "food", "dish"]):
            reply = "Our menu is available via the Food Order service. Please select option 2 from the main menu to view and order."
        else:
            # Default response: ask to choose a service
            reply = f"I didn't understand that. Please select a service from the main menu:\n1. Table Booking\n2. Food Order\n3. Party Booking\n4. Normal Chat"
            state["flow_type"] = None  # Reset flow type to go back to welcome

        self.stats["auto_replies_sent"] += 1
        return {
            "response": reply,
            "action": "restaurant_normal_chat",
            "state": state["state"]
        }

    async def _restaurant_default_reply(self, sender: str, state: dict, message: str) -> Dict[str, Any]:
        """Default reply for unimplemented restaurant flows."""
        self.stats["auto_replies_sent"] += 1
        return {
            "response": message,
            "action": "restaurant_default",
            "state": state["state"]
        }