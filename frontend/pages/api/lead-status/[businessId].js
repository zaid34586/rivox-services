const bridgeUrl = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const apiToken = process.env.ONBOARD_API_TOKEN;
  if (!apiToken) return res.status(500).json({ error: 'Server configuration error' });

  const { businessId } = req.query;
  if (!businessId) return res.status(400).json({ error: 'businessId required' });

  try {
    const resBridge = await fetch(
      `${bridgeUrl}/lead-status/${encodeURIComponent(businessId)}`,
      { method: 'GET', headers: { 'X-API-Key': apiToken } }
    );
    const data = await resBridge.json().catch(() => ({}));
    return res.status(resBridge.status).json(data);
  } catch (err) {
    console.error('lead-status API route error:', err);
    return res.status(502).json({ error: 'Failed to connect to bridge service' });
  }
}
