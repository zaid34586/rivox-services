export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridgeUrl = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';
  const apiToken = process.env.ONBOARD_API_TOKEN;

  if (!apiToken) {
    return res.status(500).json({ error: 'Server configuration error' });
  }

  try {
    const data = req.body;
    const { businessId, name, category, timezone, workingHoursStart, workingHoursEnd } = data;

    if (!businessId) {
      return res.status(400).json({ error: 'businessId is required' });
    }

    const resBridge = await fetch(`${bridgeUrl}/onboard`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiToken
      },
      body: JSON.stringify({
        businessId,
        name,
        category,
        timezone,
        workingHoursStart,
        workingHoursEnd
      })
    });

    const onboardData = await resBridge.json();
    return res.status(resBridge.status).json(onboardData);
  } catch (err) {
    console.error('Error in onboard API route:', err);
    return res.status(502).json({ error: 'Failed to connect to bridge service' });
  }
}