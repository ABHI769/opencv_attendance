# Vercel Deployment Guide

This project uses a **two-part deployment** because the face recognition backend (OpenCV, dlib, Tesseract) cannot run on Vercel serverless functions due to size and native dependency limits.

| Part | Platform | What it runs |
|------|----------|--------------|
| **Frontend** | Vercel | Web UI (HTML/JS) |
| **Backend** | Render (free) | Python Flask API + face recognition |

Your users visit your **Vercel URL**. API calls are automatically proxied to your **Render backend**.

---

## Quick Deploy (15 minutes)

### Step 1: Deploy the Backend on Render

1. Push this project to GitHub
2. Go to [render.com](https://render.com) and sign in
3. Click **New +** → **Blueprint** (or **Web Service**)
4. Connect your GitHub repo
5. Render will detect `render.yaml` and `Dockerfile` automatically
6. Click **Apply** / **Create Web Service**
7. Wait for the build to finish (5–10 minutes)
8. Copy your Render URL, e.g. `https://attendance-system-xxxx.onrender.com`

> **Tip:** On Render's free tier, the service sleeps after inactivity. The first request may take 30–60 seconds to wake up.

### Step 2: Deploy the Frontend on Vercel

**Option A — Vercel Dashboard (easiest)**

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Vercel auto-detects settings from `vercel.json`:
   - **Framework Preset:** Other
   - **Output Directory:** `frontend`
   - **Build Command:** (leave empty)
5. Add an **Environment Variable**:
   - **Name:** `BACKEND_URL`
   - **Value:** `https://attendance-system-xxxx.onrender.com` (your Render URL, no trailing slash)
6. Click **Deploy**

**Option B — Vercel CLI**

```bash
npm i -g vercel
cd ATTENDANCE
vercel
# Follow prompts, then set BACKEND_URL:
vercel env add BACKEND_URL
# Enter your Render URL when prompted
vercel --prod
```

### Step 3: Test Your Deployment

1. Open your Vercel URL (e.g. `https://your-app.vercel.app`)
2. Go to **Students** → add a student with camera
3. Go to **Session** → start an attendance session
4. Check **Reports** → generate a monthly report

If API calls fail, verify `BACKEND_URL` in Vercel → Project → Settings → Environment Variables.

---

## How It Works

```
User Browser
     │
     ▼
Vercel (frontend + API proxy)
     │  /api/* requests forwarded via api/[...path].py
     ▼
Render (Python Flask + face recognition)
```

- **Local development:** Frontend calls `http://localhost:5000/api` directly
- **Production:** Frontend calls `/api`, Vercel proxy forwards to `BACKEND_URL`

---

## Environment Variables

### Vercel

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `BACKEND_URL` | Yes | `https://attendance-system.onrender.com` | Render backend URL |

### Render

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `PYTHONUNBUFFERED` | `1` | Log output |
| `DATABASE_PATH` | `/app/ai-service/attendance.db` | SQLite path (use with persistent disk) |

---

## Troubleshooting

### "Failed to load dashboard data" on Vercel

- Confirm `BACKEND_URL` is set in Vercel environment variables
- Open `https://YOUR-RENDER-URL/api/students` in a browser — you should see `[]` or a JSON list
- Render free tier may be sleeping; wait 30–60 seconds and retry

### "BACKEND_URL is not set" error

Add `BACKEND_URL` in Vercel → Settings → Environment Variables, then redeploy.

### Face recognition slow or timing out

- Render free tier has limited CPU/RAM
- Upgrade Render plan for better performance
- Ensure good lighting when capturing faces

### CORS errors

The API proxy and Flask backend both allow cross-origin requests. If issues persist, confirm `BACKEND_URL` has no trailing slash.

### Database resets after Render redeploy

Add a **Persistent Disk** on Render (see `DEPLOYMENT.md`) mounted at `/app/ai-service` so `attendance.db` survives redeploys.

---

## Local Development

```bash
# Terminal 1 — Backend
cd ai-service
pip install -r requirements.txt
python app.py

# Terminal 2 — Frontend (optional, or open index.html)
cd frontend
python -m http.server 8000
```

Or run everything with:

```bash
python start.py
```

---

## Why Not Full Vercel?

Vercel serverless functions have strict limits that this project exceeds:

- **Bundle size:** `dlib` + `face_recognition` + OpenCV exceed the 250 MB limit
- **Native libraries:** Require system packages (cmake, tesseract, libgtk) not available on Vercel
- **Execution time:** Face recognition can exceed the 10s serverless timeout
- **File storage:** SQLite needs persistent disk; Vercel filesystem is ephemeral

Render (Docker) handles these requirements. Vercel is ideal for the static frontend and API proxy.

---

## Files Added for Vercel

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel project configuration |
| `api/[...path].py` | Proxies `/api/*` to Render backend |
| `package.json` | Vercel project metadata |
| `.vercelignore` | Excludes heavy backend files from upload |
