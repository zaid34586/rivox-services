export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridgeUrl = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';

  try {
    const resBridge = await fetch(`${bridgeUrl}/qr`, {
      method: 'GET',
    });

    if (!resBridge.ok) {
      return res.status(502).json({ error: 'Failed to fetch QR from bridge' });
    }

    const contentType = resBridge.headers.get('Content-Type') || 'image/png';
    const buffer = await resBridge.arrayBuffer();
    
    res.setHeader('Content-Type', contentType);
    res.setHeader('Cache-Control', 'no-store');
    return res.send(Buffer.from(buffer));
  } catch (err) {
    console.error('Error in qr API route:', err);
    return res.status(502).json({ error: 'Failed to connect to bridge service' });
  }
}