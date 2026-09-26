const bridgeUrl = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const apiToken = process.env.ONBOARD_API_TOKEN;
  if (!apiToken) return res.status(500).json({ error: 'Server configuration error' });

  try {
    const resBridge = await fetch(`${bridgeUrl}/reset-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiToken },
      body: JSON.stringify(req.body || {}),
    });
    const data = await resBridge.json().catch(() => ({}));
    return res.status(resBridge.status).json(data);
  } catch (err) {
    console.error('reset-session API route error:', err);
    return res.status(502).json({ error: 'Failed to connect to bridge service' });
  }
}
