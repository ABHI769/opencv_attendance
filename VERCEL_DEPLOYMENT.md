# Vercel Deployment & Architecture Guide

This project is configured for seamless deployment on **Vercel** with a decoupled AI service architecture.

| Component | Platform | Role | Why Decoupled? |
|---|---|---|---|
| **Web Frontend** | **Vercel** | Ultra-fast global static CDN (HTML/JS/Tailwind) + Node.js API Proxy | Instant delivery, 99.99% uptime, zero cold-starts |
| **AI Backend** | **Render** (or Railway / VPS) | Docker container running Python Flask, OpenCV, dlib & Face Recognition | Heavy ML models and C++ dependencies (dlib, libgl) exceed Vercel serverless 250MB limit |

---

## ⚡ Quick Deployment in 3 Steps

### Step 1: Deploy the AI Backend (Render)

1. Push your project to a GitHub repository.
2. Sign in to [render.com](https://render.com).
3. Click **New +** → **Web Service**.
4. Connect your GitHub repository.
5. Select **Docker** environment (Render detects the included `Dockerfile` automatically).
6. Plan: **Free** (or Starter for persistent database storage).
7. Under **Health Check Path**, enter: `/api/health`.
8. Click **Create Web Service**.
9. Once deployed, copy your service URL:  
   `https://attendance-system-xxxx.onrender.com`

---

### Step 2: Deploy the Web App (Vercel)

1. Sign in to [vercel.com](https://vercel.com).
2. Click **Add New** → **Project** and import your GitHub repository.
3. Vercel automatically detects the configuration from `vercel.json`:
   - **Framework Preset:** Other
   - **Output Directory:** `frontend`
   - **Build Command:** (empty)
4. Add an **Environment Variable**:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://attendance-system-xxxx.onrender.com` *(your Render URL, without trailing slash)*
5. Click **Deploy**.

> 💡 **Pro-Tip (Direct Connection Fallback):**  
> If you deploy to Vercel without setting `BACKEND_URL`, you can simply open your Vercel site, click the **Server Status** button in the top navigation, and paste your backend URL directly into the browser settings modal!

---

### Step 3: Verify Your Setup

1. Open your Vercel deployment URL (e.g., `https://your-attendance.vercel.app`).
2. Notice the **Server Status** badge in the top navigation bar:
   - 🟢 **Online:** Connected to backend.
   - 🟡 **Waking Up...:** Render free tier spins down on inactivity and takes ~30–50s to wake up on first load. The app displays an automatic countdown banner and reconnects seamlessly.
   - 🔴 **Offline:** Check backend URL configuration in Server Settings.
3. Try enrolling a student under **Students**.
4. Start a camera session under **Session** to test live face recognition.
5. Generate and export analytics under **Reports** (supports single-subject Excel and all-subjects ZIP downloads).

---

## 🛠️ Architecture & Proxy Overview

```
User's Browser (Desktop / Tablet / Mobile)
       │
       ▼
 Vercel Edge Network
   ├── Static UI: index.html (Served from Vercel CDN)
   └── Node.js Proxy: /api/[...path].js
            │
            ▼ (Encrypted HTTPS)
 Render Cloud (Dockerized Python Container)
   ├── Flask REST API (ai-service/app.py)
   ├── OpenCV + dlib Face Recognition Engine
   ├── SQLite Database (attendance.db)
   └── Tesseract OCR (ID Card Scanner)
```

### Why the Node.js Proxy?
- **Zero Cold-Starts:** Replaced the legacy Python proxy with high-speed Node.js `api/[...path].js`.
- **Streaming Support:** Supports raw binary image uploads (`multipart/form-data` and `base64`) and file downloads (`.xlsx` spreadsheets and `.zip` archives) without buffer truncation.
- **Unified CORS:** Handles cross-origin headers cleanly, eliminating duplicate header errors.
- **Resilient Timeouts:** Configured with a 60-second abort controller to smoothly handle Render free-tier cold starts.

---

## 💻 Local Development

To run the entire system locally on your machine:

```powershell
# In project root:
python start.py
```
This boots:
- Flask AI Backend on `http://localhost:5000`
- Web Frontend on `http://localhost:8000`

---

## ❓ Frequently Asked Questions

### 1. Why does Render take 30–50 seconds on first request?
On Render's free tier, the container sleeps after 15 minutes of inactivity. Our UI detects this state automatically, displays a friendly "Waking up..." banner, and auto-polls until the service is active. To prevent sleeping, you can upgrade to Render's $7/month plan or set up a free cron pinger (e.g. UptimeRobot) targeting `/api/health`.

### 2. Can I use persistent storage for the database?
Yes! On Render Starter plan or any Docker host (like Railway or DigitalOcean), mount a persistent disk to `/data` and set the environment variable `DATABASE_PATH=/data/attendance.db`. On the free tier, the database persists as long as the container is running.
