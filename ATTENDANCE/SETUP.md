# Face Recognition Attendance System - Setup Guide

## 🚀 Quick Start

### Option 1: Easy Launch (Recommended)
1. Double-click `RUN.bat` file
2. Wait for servers to start
3. Browser will open automatically at http://localhost:8080

### Option 2: Manual Launch
1. Open Command Prompt in this directory
2. Run: `python start.py`
3. Browser will open automatically

## 📋 Requirements

- **Python 3.8+** installed
- **Camera** for face recognition
- **Modern browser** (Chrome, Firefox, Edge)

## 🔧 Installation (if needed)

If dependencies are missing, run:
```bash
pip install -r ai-service/requirements.txt
```

## 🌐 Access Points

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:5000

## 🎯 How to Use

### 1. Add Students
- Go to **Students** tab
- Fill in student details
- Capture face photo using camera
- Click "Save Student"

### 2. Take Attendance
- Go to **Session** tab
- Enter class name and duration
- Click "Start Detection"
- System will automatically recognize faces and mark attendance

### 3. View Reports
- Go to **Reports** tab
- Select month and year
- Click "Generate View"
- Download Excel/CSV report

## 🛠️ Troubleshooting

### Backend Not Starting
- Make sure Python is installed
- Check if port 5000 is available
- Install dependencies: `pip install -r ai-service/requirements.txt`

### Frontend Not Loading
- Check if port 8080 is available
- Make sure backend is running first

### Camera Not Working
- Check browser camera permissions
- Make sure camera is not used by another app
- Try refreshing the page

### Face Recognition Not Working
- Ensure good lighting
- Face should be clearly visible
- Add students with clear face photos first

## 📁 Project Structure

```
ATTENDANCE/
├── start.py          # Main startup script
├── RUN.bat           # Windows batch file
├── frontend/         # Web interface
│   └── index.html    # Main web page
├── ai-service/       # Backend API
│   ├── app.py        # Flask server
│   ├── requirements.txt
│   └── attendance.db # SQLite database
└── SETUP.md          # This file
```

## 🔒 Security Notes

- System runs locally (no internet required)
- Face data stored locally in database
- No data is sent to external servers

## 📞 Support

If you encounter issues:
1. Check that both servers are running
2. Verify camera permissions
3. Ensure all dependencies are installed
4. Try restarting both servers

---

**System Status**: ✅ Ready to use
**Last Updated**: 2026-04-05
