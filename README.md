# Face Recognition Attendance System 📸🎓

A production-ready, AI-powered attendance management web application that utilizes biometric facial recognition and OCR document scanning to automate student attendance tracking. 

Built with a modern decoupled architecture: **Vercel** delivers an ultra-fast global frontend with a Node.js edge proxy, connected to a **Dockerized Python Flask AI backend** (deployable on Render, Railway, or VPS) running OpenCV, dlib, and Tesseract OCR.

---

## 🌟 Key Features

- **Real-Time Facial Recognition**: Automated face detection and matching using `face_recognition` and OpenCV with live bounding boxes.
- **Smart Concurrency Guard**: Client-side throttle prevents webcam request pileup and ensures smooth, low-latency video streaming.
- **ID Card OCR Scanning**: Auto-extracts student name and roll number directly from student ID card photo uploads using Tesseract OCR.
- **Academic Subject Management**: Create, assign, and manage custom subjects dynamically with the "+ Add Subject" modal.
- **Active Session Tracking**: Configurable session durations, real-time present/absent marking, and auto-marking absentees upon session close.
- **Rich Analytics & Multi-Format Exports**: 
  - Interactive monthly summary table.
  - Download individual subject attendance reports as formatted Excel spreadsheets (`.xlsx`).
  - Download all subject reports bundled in a single `.zip` archive.
- **Live Server Status Indicator**: 
  - 🟢 **Online** | 🟡 **Waking Up (Cold Start)** | 🔴 **Offline**
  - Displays real-time connection status with auto-retry and cold-start countdown banner.
- **Dynamic Backend Switcher**: In-browser server configuration modal to test and switch backend URLs on the fly without redeploying frontend code.

---

## 🏛️ System Architecture

```
                       ┌─────────────────────────────────────────┐
                       │               User Browser              │
                       │     (Webcam Feed / HTML5 / Modern CSS)  │
                       └────────────────────┬────────────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │          Vercel Edge Network            │
                       │  ├── Static Assets: frontend/ (CDN)     │
                       │  └── Node.js Proxy: api/[...path].js    │
                       └────────────────────┬────────────────────┘
                                            │  HTTPS (Streaming Proxy)
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │         Render / Cloud Container        │
                       │               (Dockerfile)              │
                       │  ├── Flask API Service (ai-service/)    │
                       │  ├── OpenCV & dlib (face_recognition)   │
                       │  ├── Tesseract OCR (ID Card Scanner)    │
                       │  └── SQLite Database (attendance.db)    │
                       └─────────────────────────────────────────┘
```

### Why Decoupled?
Vercel Serverless Functions enforce a **250MB limit** and a **10-second execution cap**, making heavy C++ machine learning packages (`dlib`, `face_recognition`, `opencv-python-headless`) incompatible with native Vercel runtime. By deploying the Python AI engine in a lightweight Docker container on Render or Railway, and proxying through Vercel's Node.js edge runtime, you get the best of both worlds: **instant global frontend delivery** and **unrestricted AI compute power**.

---

## 🚀 How to Deploy on Vercel

Deploying takes under 5 minutes using the two-tier setup.

### Step 1: Deploy the AI Backend (Render)

1. Push this repository to your **GitHub** account.
2. Go to [Render.com](https://render.com) and log in.
3. Click **New +** → **Web Service**.
4. Select **Build and deploy from a Git repository** and pick your repo.
5. Configure the service:
   - **Name:** `attendance-ai-backend` (or your preferred name)
   - **Region:** Closest to your users (e.g., Oregon, Frankfurt, Singapore)
   - **Language / Environment:** **Docker** (Render will automatically detect the root `Dockerfile`)
   - **Instance Type:** **Free** (or Starter for persistent disk)
   - **Health Check Path:** `/api/health`
6. Click **Create Web Service**.
7. Wait ~3–5 minutes for Docker build and deployment to complete.
8. Copy your Render URL (e.g., `https://attendance-ai-backend-xxxx.onrender.com`).

---

### Step 2: Deploy the Web Frontend (Vercel)

1. Go to [Vercel.com](https://vercel.com) and log in.
2. Click **Add New...** → **Project**.
3. Import your GitHub repository.
4. In the configuration screen:
   - **Framework Preset:** `Other`
   - **Root Directory:** `./`
   - **Output Directory:** `frontend`
   - **Build Command:** *(Leave empty)*
5. Expand the **Environment Variables** section and add:
   - **Key:** `BACKEND_URL`
   - **Value:** `https://attendance-ai-backend-xxxx.onrender.com` *(your Render backend URL without trailing slash)*
6. Click **Deploy**.

> 💡 **Client-Side Override Fallback:**  
> If you deploy to Vercel without configuring environment variables, you can simply open your live Vercel app, click the **Server Status** badge in the top navigation bar, enter your backend URL, click **Test & Save**, and the application will connect directly!

---

### Step 3: Test and Verify Live Deployment

1. Visit your Vercel URL (e.g., `https://attendance-system.vercel.app`).
2. Check the **Server Status** pill in the top header:
   - 🟢 **Online:** The edge proxy and AI backend are communicating.
   - 🟡 **Waking Up...:** If Render's free tier has gone idle (spins down after 15 min), the app displays a countdown banner and will reconnect automatically within ~45s.
3. Navigate to **Students** and register a student using either webcam capture or ID card OCR.
4. Navigate to **Session**, select a subject, start face detection, and verify live recognition.
5. Check **Reports** to view records and export single-subject Excel (`.xlsx`) or all-subject archives (`.zip`).

---

## 💻 Local Development Setup

You can run the entire system locally without Docker.

### Prerequisites
- Python 3.8+
- Node.js 18+ (optional, for local Vercel CLI testing)
- Webcam connected to your computer
- Tesseract OCR installed on your machine:
  - **Windows:** [UB-Mannheim Installer](https://github.com/UB-Mannheim/tesseract/wiki) (default: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
  - **macOS:** `brew install tesseract`
  - **Linux:** `sudo apt-get install tesseract-ocr`

### 1-Click Startup (Recommended)
From the project root directory, run:
```powershell
python start.py
```
This automatically initializes:
- **Flask AI Service:** `http://localhost:5000`
- **Frontend HTTP Server:** `http://localhost:8000`

### Manual Startup

**Terminal 1 (AI Service):**
```bash
cd ai-service
pip install -r requirements.txt
python app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
python -m http.server 8000
```
Then open `http://localhost:8000` in your web browser.

### Docker Local Run
To test the production container locally:
```bash
docker build -t attendance-ai .
docker run -p 5000:5000 attendance-ai
```

---

## 📁 Project Structure

```
ATTENDANCE/
├── Dockerfile              # Production container (Debian, dlib, OpenCV, Tesseract)
├── vercel.json             # Vercel routing configuration
├── package.json            # Node.js engine specification for Vercel proxy
├── render.yaml             # Render Blueprint specification
├── start.py                # Dual local development runner
│
├── api/                    # Vercel Serverless Edge API
│   └── [...path].js        # Streaming Node.js reverse proxy to AI Backend
│
├── ai-service/             # Core Python Backend
│   ├── app.py              # Flask server, Face Recognition & OCR routes
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Static Web Client
│   ├── index.html          # SPA layout with modals & server indicator
│   ├── styles.css          # Design system & dark mode aesthetics
│   └── script.js           # Camera controller, face detection loop, API client
│
└── VERCEL_DEPLOYMENT.md    # Dedicated cloud deployment guide
```

---

## 📡 REST API Reference

All routes are accessible via `/api/*` either directly on the Python backend or routed through the Vercel proxy.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Healthcheck and backend status |
| `GET` | `/api/students` | List all registered students |
| `POST` | `/api/students` | Enroll student with name, roll number, and face encoding |
| `DELETE` | `/api/students/<id>` | Delete student record |
| `POST` | `/api/scan-id-card` | OCR analysis of uploaded student ID image |
| `GET` | `/api/subjects` | List academic subjects |
| `POST` | `/api/subjects` | Add new subject |
| `DELETE` | `/api/subjects/<id>` | Delete subject |
| `GET` | `/api/sessions` | List attendance sessions |
| `POST` | `/api/sessions` | Create new attendance session |
| `POST` | `/api/sessions/<id>/start` | Activate camera recognition session |
| `POST` | `/api/sessions/<id>/end` | Close session and auto-mark absentees |
| `POST` | `/api/recognize-faces` | Match face encoding against enrolled student database |
| `GET` | `/api/reports/monthly?month=YYYY-MM` | Fetch monthly attendance JSON matrix |
| `GET` | `/api/reports/excel?month=YYYY-MM&subject=X` | Download subject Excel spreadsheet (`.xlsx`) |
| `GET` | `/api/reports/subject-excel?month=YYYY-MM` | Download all subject reports bundled as `.zip` |

---

## 🔧 Troubleshooting & FAQs

### Why does Render take 30–50 seconds on first request?
On Render's Free tier, the container spins down into sleep mode after 15 minutes of inactivity. When a request arrives, it takes ~30–50 seconds to spin up. The frontend automatically detects this, presents a cold-start countdown banner, and auto-reconnects when the server is ready. To keep it warm 24/7, you can use a free pinging service (like UptimeRobot) targeting `/api/health` every 10 minutes.

### Camera permissions blocked in browser?
Modern browsers enforce secure contexts for webcam access (`navigator.mediaDevices.getUserMedia`):
- Localhost (`http://localhost:*`) is always permitted.
- Remote deployments require **HTTPS** (which Vercel provides automatically).
- Make sure to allow camera permissions when prompted by your browser.

### Face recognition accuracy tips:
- Ensure adequate, even frontal lighting without heavy backlighting.
- Position camera at eye level.
- Face should occupy at least 20% of the camera frame during registration.

---

## 📄 License
This project is open source and created for academic and attendance management workflows. Please ensure compliance with local data privacy regulations regarding biometric storage.
