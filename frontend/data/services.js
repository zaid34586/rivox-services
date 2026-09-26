export const contactWhatsApp = '919899359566';
export const UPI_ID = 'rivox@upi';
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
      'Ek smart AI agent jo aapke WhatsApp pe har customer ka handle karta hai — bookings leta hai, orders lete hain, reminders bhejta hai aur reviews collect karta hai. Aapko sirf apna WhatsApp scan karna hai.',
    features: [
      { icon: '⚡', title: '24/7 Instant Replies', text: 'Har message ka turant jawab — customer kabhi wait nahi karega.' },
      { icon: '🍽️', title: 'Table & Party Bookings', text: 'Booking le kar confirm, calendar me entry aur auto reminder.' },
      { icon: '🛒', title: 'Food Orders', text: 'Menu se order lena, confirm karna aur status update — sab automatic.' },
      { icon: '💬', title: 'FAQ Auto-Reply', text: 'Timing, location, payment — common sawaalon ke sahi jawab.' },
      { icon: '🔔', title: 'Reminders & Follow-ups', text: 'Booking reminder aur service ke baad follow-up message.' },
      { icon: '⭐', title: 'Reviews & Feedback', text: 'Service ke baad feedback maangta hai — rating badhti hai.' },
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
