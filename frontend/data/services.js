export const contactWhatsApp = '919899359566';
export const UPI_ID = '9899359566@sbi';
export const UPI_AMOUNT = '2,000';

export const services = [
  {
    id: 'whatsapp',
    title: 'WhatsApp AI Agent',
    name: 'WhatsApp AI Agent',
    icon: '🤖',
    tagline: 'Your business never sleeps. Replies, bookings, orders & feedback — automatic, 24/7.',
    price: '₹2,000–5,000/month',
    priceNote: 'Free setup · scan & start testing in minutes',
    description:
      'A smart AI agent that handles every customer on your WhatsApp — takes bookings, places orders, sends reminders and collects reviews. All you do is scan your WhatsApp.',
    features: [
      { icon: '⚡', title: '24/7 Instant Replies', text: 'Instant reply to every message — customers never have to wait.' },
      { icon: '🍽️', title: 'Table & Party Bookings', text: 'Takes the booking, confirms it, adds it to the calendar and sends an auto reminder.' },
      { icon: '🛒', title: 'Food Orders', text: 'Takes orders from the menu, confirms them and sends status updates — all automatic.' },
      { icon: '💬', title: 'FAQ Auto-Reply', text: 'Correct answers to common questions about timing, location and payment.' },
      { icon: '🔔', title: 'Reminders & Follow-ups', text: 'Booking reminders and a follow-up message after the service.' },
      { icon: '⭐', title: 'Reviews & Feedback', text: 'Asks for feedback after the service — so your rating keeps growing.' },
    ],
    categoryOptions: [
      { value: 'restaurant', label: '🍽️ Restaurant / Cafe' },
      { value: 'salon', label: '💇 Salon / Spa' },
      { value: 'clinic', label: '🏥 Clinic / Healthcare' },
      { value: 'retail', label: '🛍️ Retail Store' },
      { value: 'gym', label: '🏋️ Gym / Fitness' },
      { value: 'home_services', label: '🔧 Home Services' },
      { value: 'other', label: '📦 Other' },
    ],
    serviceOptions: [
      { value: 'table_booking', label: 'Table Bookings' },
      { value: 'food_order', label: 'Food Ordering' },
      { value: 'party_booking', label: 'Party / Birthday Booking' },
      { value: 'normal_chat', label: 'FAQ Auto-Reply' },
    ],
  },
];
