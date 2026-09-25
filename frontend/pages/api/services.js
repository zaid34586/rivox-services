export default function handler(req, res) {
  const services = [
    { id: 'whatsapp', title: 'WhatsApp Automation', description: 'Auto-reply, booking, reminders, follow-up, review collection for local businesses.', price: '₹2,000–5,000/month' },
    { id: 'leadfinder', title: 'Lead Finder', description: 'Find international businesses (US/UK/CA/AU) by category and location.', price: '₹1,500/month' },
    { id: 'contentfactory', title: 'Content Factory', description: 'AI-generated posts, reels, stories, captions, hashtags.', price: '₹3,000/month' },
    { id: 'editor', title: 'Editor Agent', description: 'SEO optimization, A/B variants, accessibility, compliance.', price: 'Included with Content Factory' },
    { id: 'delivery', title: 'Delivery Agent', description: 'Scheduled publishing to IG, FB, YT, TT, LI, X with retry.', price: '₹1,000/month' },
  ];
  res.status(200).json(services);
}
