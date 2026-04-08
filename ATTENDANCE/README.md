# Face Recognition Attendance System

A comprehensive attendance management system that uses face recognition technology to automatically mark student attendance. The system captures student faces, generates unique facial encodings, and tracks attendance in real-time during scheduled sessions.

## Features

- **Face Recognition**: Automatic face detection and recognition using OpenCV and face_recognition library
- **Student Management**: Add, delete, and manage student profiles with facial data
- **ID Card Scanning**: OCR-powered student registration from ID card images
- **Subject Management**: Organize attendance by subjects with separate Excel reports
- **Real-time Attendance**: Live camera feed with automatic face recognition during attendance sessions
- **Session Management**: Create and manage attendance sessions with customizable duration
- **Monthly Reports**: Generate and download monthly attendance reports in Excel format
- **Subject-specific Reports**: Download separate Excel files for each subject
- **Admin Interface**: Clean, responsive web interface for system administration
- **Database Storage**: SQLite database for persistent data storage

## System Architecture

```
ATTENDANCE/
├── ai-service/          # Python Flask API with face recognition
│   ├── app.py          # Main application server
│   └── requirements.txt # Python dependencies
├── frontend/           # HTML/CSS/JavaScript web interface
│   ├── index.html      # Main web page
│   ├── styles.css      # Styling
│   └── script.js       # Frontend logic
└── README.md          # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Modern web browser with camera support
- Windows/Linux/macOS

### Step 1: Install Python Dependencies

Navigate to the `ai-service` directory and install required packages:

```bash
cd ai-service
pip install -r requirements.txt
```

**Note**: The system now includes OCR functionality which requires Tesseract OCR engine. Download and install it from:
- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

**Note**: The `face_recognition` library may require additional system dependencies:

**On Windows:**
```bash
# Install Visual Studio Build Tools or C++ compiler
# Install CMake
pip install --upgrade setuptools wheel
pip install dlib
```

**On macOS:**
```bash
brew install cmake
pip install dlib
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev
pip install dlib
```

### Step 2: Start the AI Service

```bash
cd ai-service
python app.py
```

The server will start on `http://localhost:5000`

### Step 3: Open the Frontend

Open the `frontend/index.html` file in your web browser:

```bash
# Simply open the file in your browser
# Or use a simple HTTP server for better development experience
cd frontend
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

## Usage

### 1. Add Students

**Option A: Manual Entry**
1. Navigate to the **Students** section
2. Click "Start Camera" to enable webcam
3. Enter student name and roll number
4. Click "Capture Photo" to take a picture
5. Click "Add Student" to save the student with facial encoding

**Option B: ID Card Scanning**
1. Navigate to the **Students** section
2. Click "Scan ID Card" button
3. Upload ID card image (JPG/PNG)
4. Click "Scan & Extract" to automatically read name and roll number
5. System auto-fills the form fields using OCR
6. Add face photo and click "Add Student"

### 2. Start Attendance Session

1. Navigate to the **Attendance** section
2. Select subject from dropdown (e.g., "Data Structures", "Algorithms")
3. Enter session name (e.g., "Lecture 1", "Mid-term", "Quiz")
4. Set duration in hours (default: 1 hour)
5. Click "Start Detection" to create and activate the session
6. The system will automatically detect faces and mark attendance

### 3. Monitor Attendance

- Live camera feed shows recognized faces
- Recognized students appear in the "Recognized Students" list
- Attendance is automatically marked as "Present" for recognized faces
- Unrecognized students are marked as "Absent" when the session ends

### 4. End Session

1. Click "End Session" to stop the attendance session
2. All students not marked as "Present" will be automatically marked as "Absent"
3. Session data is saved to the database

### 5. Generate Reports

**Option A: General Reports**
1. Navigate to the **Reports** section
2. Select month you want to generate a report for
3. Click "Generate Monthly Report"
4. View the attendance table with present/absent status
5. Click "Download Excel" to get the report in Excel format

**Option B: Subject-specific Reports**
1. Navigate to the **Reports** section
2. Select month and specific subject (e.g., "Data Structures")
3. Click "Download Excel" to get subject-specific report
4. Files are named with subject prefix (e.g., `attendance_report_Data_Structures_2026-04.xlsx`)

**Option C: All Subjects Report**
1. Use the "Download All Subjects" option to get ZIP file
2. Contains separate Excel files for each subject
3. Each file is named with subject prefix for easy organization

## API Endpoints

### Students
- `GET /api/students` - Get all students
- `POST /api/students` - Add new student
- `DELETE /api/students/{id}` - Delete student

### Sessions
- `GET /api/sessions` - Get all sessions
- `POST /api/sessions` - Create new session
- `POST /api/sessions/{id}/start` - Start/activate a session
- `POST /api/sessions/{id}/mark-attendance` - Mark attendance
- `POST /api/sessions/{id}/end` - End session
- `GET /api/attendance/{session_id}` - Get attendance records

### Subjects
- `GET /api/subjects` - Get all subjects
- `POST /api/subjects` - Add new subject
- `DELETE /api/subjects/{id}` - Delete subject

### ID Card Scanning
- `POST /api/scan-id-card` - Extract student info from ID card image using OCR

### Face Recognition
- `POST /api/recognize-faces` - Recognize faces from image

### Reports
- `GET /api/reports/monthly?month=YYYY-MM` - Get monthly report
- `GET /api/reports/excel?month=YYYY-MM&subject=SubjectName` - Download subject-specific Excel report
- `GET /api/reports/subject-excel?month=YYYY-MM` - Download all subjects as ZIP file

## Database Schema

### Students Table
- `id` - Primary key
- `name` - Student name
- `roll_number` - Unique roll number
- `encoding` - Facial encoding (JSON)
- `image_path` - Path to stored image (optional)
- `created_at` - Timestamp

### Subjects Table
- `id` - Primary key
- `name` - Subject name (unique)
- `created_at` - Creation timestamp

### Attendance Sessions Table
- `id` - Primary key
- `session_name` - Session identifier
- `subject` - Subject name (foreign key reference)
- `start_time` - Session start time
- `end_time` - Session end time
- `duration_hours` - Session duration
- `is_active` - Session status (0 = inactive, 1 = active)
- `created_at` - Creation timestamp

### Attendance Records Table
- `id` - Primary key
- `session_id` - Foreign key to sessions
- `student_id` - Foreign key to students
- `status` - 'present' or 'absent'
- `marked_at` - Timestamp when marked

## Security Considerations

- Camera access requires user permission
- Facial encodings are stored securely in the database
- No images are stored permanently (only encodings)
- Admin interface should be protected in production
- Use HTTPS in production environments

## Troubleshooting

### Camera Not Working
- Ensure browser has camera permissions
- Check if camera is not being used by another application
- Try refreshing the page and granting camera permissions again

### Face Recognition Issues
- Ensure good lighting conditions
- Face should be clearly visible and facing the camera
- Try recapturing student photos if recognition is poor
- Check if multiple faces are in the frame (system works best with single faces)

### Installation Issues
- Make sure Python 3.8+ is installed
- Install system dependencies for dlib/face_recognition
- Use virtual environment to avoid conflicts

## Performance Tips

- Good lighting improves face recognition accuracy
- Position camera at eye level for best results
- Ensure consistent lighting during registration and attendance
- Regular database cleanup for old sessions

## Recent Enhancements (✅ Completed)

- **ID Card Scanning**: OCR-powered student registration from ID cards
- **Subject Management**: Organize attendance by academic subjects
- **Subject-specific Reports**: Separate Excel files for each subject
- **Session Control**: Sessions only activate on user command
- **Improved Database Schema**: Better data organization and integrity

## Future Enhancements

- Multi-camera support
- Batch student registration
- Email notifications for parents
- Mobile app support
- Cloud storage integration
- Advanced analytics and reporting

## License
This project is for educational purposes. Please ensure compliance with local privacy laws and regulations when implementing facial recognition systems.
