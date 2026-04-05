import os
import cv2
import face_recognition
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import base64
import pandas as pd
from io import BytesIO
import calendar

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            encoding TEXT NOT NULL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reset auto-increment if students table is empty
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    if student_count == 0:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='students'")
    
    # Attendance sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_hours INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Attendance records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
            FOREIGN KEY (student_id) REFERENCES students (id),
            UNIQUE(session_id, student_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

class FaceRecognitionService:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_roll_numbers = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known faces from database"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, roll_number, encoding FROM students")
        students = cursor.fetchall()
        
        self.known_encodings = []
        self.known_names = []
        self.known_roll_numbers = []
        
        for name, roll_number, encoding_str in students:
            try:
                encoding = np.array(json.loads(encoding_str))
                self.known_encodings.append(encoding)
                self.known_names.append(name)
                self.known_roll_numbers.append(roll_number)
            except:
                continue
        
        conn.close()
    
    def detect_faces(self, frame):
        """Detect faces in a frame and return face locations"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        return face_locations
    
    def recognize_faces(self, frame):
        """Recognize faces in a frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_students = []
        
        for face_encoding in face_encodings:
            if len(self.known_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.6)
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        recognized_students.append({
                            'name': self.known_names[best_match_index],
                            'roll_number': self.known_roll_numbers[best_match_index],
                            'confidence': float(1 - face_distances[best_match_index])
                        })
        
        return recognized_students

# Global face recognition service
face_service = FaceRecognitionService()

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, roll_number, image_path FROM students")
    students = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': row[0],
        'name': row[1],
        'roll_number': row[2],
        'image_path': row[3]
    } for row in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    """Add a new student with face encoding"""
    try:
        data = request.json
        print(f"Received data: {data.keys()}")
        
        name = data['name']
        roll_number = data['roll_number']
        image_data = data['image']  # Base64 encoded image
        
        print(f"Processing student: {name}, {roll_number}")
        print(f"Image data length: {len(image_data)}")
        print(f"Image data starts with: {image_data[:50]}")
        
        # Decode base64 image
        if ',' in image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
        else:
            image_bytes = base64.b64decode(image_data)
            
        print(f"Decoded image bytes: {len(image_bytes)}")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode image")
            return jsonify({'error': 'Failed to decode image'}), 400
            
        print(f"Image shape: {img.shape}")
        
        # Generate face encoding
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img)
        
        if len(face_locations) == 0:
            print("No face detected in the image")
            return jsonify({'error': 'No face detected in the image'}), 400
        
        print(f"Found {len(face_locations)} face(s)")
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        encoding = face_encodings[0]
        
        # Save to database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, roll_number, encoding) VALUES (?, ?, ?)",
            (name, roll_number, json.dumps(encoding.tolist()))
        )
        conn.commit()
        conn.close()
        
        print(f"Student {name} added successfully")
        
        # Reload known faces
        face_service.load_known_faces()
        
        return jsonify({'message': 'Student added successfully'})
    
    except Exception as e:
        print(f"Error adding student: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new attendance session"""
    try:
        data = request.json
        session_name = data['session_name']
        duration_hours = data.get('duration_hours', 1)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO attendance_sessions (session_name, start_time, end_time, duration_hours, is_active) VALUES (?, ?, ?, ?, ?)",
            (session_name, start_time, end_time, duration_hours, True)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'session_name': session_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': duration_hours
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/mark-attendance', methods=['POST'])
def mark_attendance(session_id):
    """Mark attendance for recognized faces"""
    try:
        data = request.json
        recognized_students = data['recognized_students']
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Check if session is active
        cursor.execute("SELECT is_active FROM attendance_sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session or not session[0]:
            return jsonify({'error': 'Session is not active'}), 400
        
        # Mark attendance for recognized students
        for student in recognized_students:
            cursor.execute("SELECT id FROM students WHERE roll_number = ?", (student['roll_number'],))
            student_record = cursor.fetchone()
            
            if student_record:
                cursor.execute(
                    "INSERT OR REPLACE INTO attendance_records (session_id, student_id, status) VALUES (?, ?, ?)",
                    (session_id, student_record[0], 'present')
                )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Attendance marked successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    """End an attendance session and mark absent students"""
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Mark session as inactive
        cursor.execute("UPDATE attendance_sessions SET is_active = 0, end_time = ? WHERE id = ?", 
                      (datetime.now(), session_id))
        
        # Get all students
        cursor.execute("SELECT id FROM students")
        all_students = cursor.fetchall()
        
        # Mark absent students who weren't marked present
        for student in all_students:
            cursor.execute(
                "INSERT OR IGNORE INTO attendance_records (session_id, student_id, status) VALUES (?, ?, ?)",
                (session_id, student[0], 'absent')
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session ended successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all attendance sessions"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance_sessions ORDER BY created_at DESC")
    sessions = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': row[0],
        'session_name': row[1],
        'start_time': row[2],
        'end_time': row[3],
        'duration_hours': row[4],
        'is_active': row[5],
        'created_at': row[6]
    } for row in sessions])

@app.route('/api/attendance/<int:session_id>', methods=['GET'])
def get_attendance(session_id):
    """Get attendance records for a session"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.name, s.roll_number, ar.status, ar.marked_at
        FROM attendance_records ar
        JOIN students s ON ar.student_id = s.id
        WHERE ar.session_id = ?
        ORDER BY s.name
    ''', (session_id,))
    
    records = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'name': row[0],
        'roll_number': row[1],
        'status': row[2],
        'marked_at': row[3]
    } for row in records])

@app.route('/api/recognize-faces', methods=['POST'])
def recognize_faces():
    """Recognize faces from an image"""
    try:
        data = request.json
        image_data = data['image']
        session_id = data.get('session_id')
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Recognize faces
        recognized_students = face_service.recognize_faces(img)
        
        return jsonify({'recognized_students': recognized_students})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/monthly', methods=['GET'])
def get_monthly_report():
    """Generate monthly attendance report"""
    try:
        month = request.args.get('month')
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400
        
        # Parse month (YYYY-MM format)
        year, month_num = map(int, month.split('-'))
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month_num)[1]
        days = [f"{year}-{month_num:02d}-{day:02d}" for day in range(1, num_days + 1)]
        
        # Get all students
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_number FROM students ORDER BY roll_number")
        students = cursor.fetchall()
        
        # Get attendance for each student for each day
        report_data = {
            'days': [day.split('-')[2] for day in days],  # Just day numbers
            'students': []
        }
        
        for student_id, name, roll_number in students:
            student_attendance = {}
            
            for day in days:
                cursor.execute('''
                    SELECT ar.status 
                    FROM attendance_records ar
                    JOIN attendance_sessions s ON ar.session_id = s.id
                    WHERE ar.student_id = ? AND DATE(s.start_time) = ?
                ''', (student_id, day))
                
                records = cursor.fetchall()
                
                if records:
                    # If there are multiple sessions on the same day, consider present if any session has present
                    if any(record[0] == 'present' for record in records):
                        student_attendance[day.split('-')[2]] = 'present'
                    else:
                        student_attendance[day.split('-')[2]] = 'absent'
                else:
                    student_attendance[day.split('-')[2]] = None
            
            report_data['students'].append({
                'id': student_id,
                'name': name,
                'roll_number': roll_number,
                'attendance': student_attendance
            })
        
        conn.close()
        return jsonify(report_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/excel', methods=['GET'])
def download_excel_report():
    """Download monthly attendance report as Excel file"""
    try:
        month = request.args.get('month')
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400
        
        # Parse month (YYYY-MM format)
        year, month_num = map(int, month.split('-'))
        
        # Get all days in the month
        num_days = calendar.monthrange(year, month_num)[1]
        days = [f"{year}-{month_num:02d}-{day:02d}" for day in range(1, num_days + 1)]
        
        # Get all students
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_number FROM students ORDER BY roll_number")
        students = cursor.fetchall()
        
        # Create Excel data
        excel_data = []
        headers = ['Roll Number', 'Name'] + [f"Day {day}" for day in range(1, num_days + 1)] + ['Total Present', 'Percentage']
        excel_data.append(headers)
        
        for student_id, name, roll_number in students:
            row = [roll_number, name]
            total_present = 0
            
            for day in days:
                cursor.execute('''
                    SELECT ar.status 
                    FROM attendance_records ar
                    JOIN attendance_sessions s ON ar.session_id = s.id
                    WHERE ar.student_id = ? AND DATE(s.start_time) = ?
                ''', (student_id, day))
                
                records = cursor.fetchall()
                
                if records:
                    # If there are multiple sessions on the same day, consider present if any session has present
                    if any(record[0] == 'present' for record in records):
                        row.append('P')
                        total_present += 1
                    else:
                        row.append('A')
                else:
                    row.append('-')
            
            # Add totals
            percentage = (total_present / num_days * 100) if num_days > 0 else 0
            row.extend([total_present, f"{percentage:.1f}%"])
            excel_data.append(row)
        
        conn.close()
        
        # Create Excel file
        df = pd.DataFrame(excel_data[1:], columns=excel_data[0])
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=f'attendance_report_{month}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Delete attendance records first
        cursor.execute("DELETE FROM attendance_records WHERE student_id = ?", (student_id,))
        
        # Delete student
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        
        conn.commit()
        conn.close()
        
        # Reload known faces
        face_service.load_known_faces()
        
        return jsonify({'message': 'Student deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
