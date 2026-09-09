/**
 * Vercel Serverless Function: API Proxy
 * Forwards /api/* requests to your Python backend (e.g. deployed on Render, Railway, etc.)
 * 
 * Set BACKEND_URL in your Vercel Project Settings -> Environment Variables.
 * Example: BACKEND_URL = https://attendance-system.onrender.com
 */

export const config = {
  api: {
    bodyParser: false, // Disabling bodyParser allows raw stream forwarding (essential for file uploads and downloads)
    responseLimit: false,
  },
};

export default async function handler(req, res) {
  // Always handle CORS preflight requests first
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  const backendUrl = process.env.BACKEND_URL ? process.env.BACKEND_URL.replace(/\/+$/, '') : null;

  if (!backendUrl) {
    return res.status(503).json({
      error: 'BACKEND_URL is not set on Vercel.',
      message: 'Please set BACKEND_URL in your Vercel project Settings -> Environment Variables (e.g. https://your-backend.onrender.com). Alternatively, open the Settings modal in the web app to connect directly to your backend URL.',
      configured: false
    });
  }

  // Construct target URL
  // req.url contains full path e.g. /api/students or /api/reports/monthly?month=2026-09
  const targetPath = req.url.startsWith('/') ? req.url : `/${req.url}`;
  const targetUrl = `${backendUrl}${targetPath}`;

  try {
    // Read request body if present (POST, PUT, PATCH, DELETE)
    let bodyData = null;
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method)) {
      const chunks = [];
      for await (const chunk of req) {
        chunks.push(chunk);
      }
      if (chunks.length > 0) {
        bodyData = Buffer.concat(chunks);
      }
    }

    // Forward relevant headers
    const forwardHeaders = {};
    const skipHeaders = ['host', 'connection', 'content-length', 'transfer-encoding'];
    for (const [key, value] of Object.entries(req.headers)) {
      if (!skipHeaders.includes(key.toLowerCase())) {
        forwardHeaders[key] = value;
      }
    }

    // Set request timeout to 60s (handles Render cold-starts)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const backendResponse = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: bodyData,
      signal: controller.signal,
      redirect: 'follow',
    });

    clearTimeout(timeoutId);

    // Forward response headers (excluding hop-by-hop headers and duplicate CORS)
    const skipResponseHeaders = ['transfer-encoding', 'connection', 'access-control-allow-origin'];
    backendResponse.headers.forEach((val, key) => {
      if (!skipResponseHeaders.includes(key.toLowerCase())) {
        res.setHeader(key, val);
      }
    });

    // Ensure single CORS header
    res.setHeader('Access-Control-Allow-Origin', '*');

    // Get response body as buffer and send with proper status
    const arrayBuffer = await backendResponse.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    res.status(backendResponse.status).send(buffer);

  } catch (error) {
    console.error('API Proxy Error:', error);

    const isTimeout = error.name === 'AbortError';
    const statusCode = isTimeout ? 504 : 502;

    return res.status(statusCode).json({
      error: isTimeout ? 'Gateway Timeout' : 'Bad Gateway',
      message: isTimeout
        ? 'The backend server took longer than 60s to respond. If running on Render free tier, it may still be waking up. Please retry in a few seconds.'
        : `Could not reach backend server at ${backendUrl}. Ensure the backend is active and reachable. Error: ${error.message}`,
      targetUrl,
      isWakeUpCandidate: true
    });
  }
}
