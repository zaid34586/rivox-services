export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { businessId } = req.query;
  const bridgeUrl = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';
  const apiToken = process.env.ONBOARD_API_TOKEN;

  if (!apiToken) {
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const resBridge = await fetch(`${bridgeUrl}/verify-session/${businessId}`, {
      method: 'GET',
      headers: {
        'X-API-Key': apiToken
      }
    });

    const data = await resBridge.json();
    return res.status(resBridge.status).json(data);
  } catch (err) {
    console.error('Error in verify-session API route:', err);
    return res.status(502).json({ error: 'Failed to connect to bridge service' });
  }
}