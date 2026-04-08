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
import pytesseract
import re
from PIL import Image

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
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
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    if student_count == 0:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='students'")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_name TEXT NOT NULL,
            subject TEXT DEFAULT 'General',
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_hours INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("PRAGMA table_info(attendance_sessions)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'subject' not in columns:
        cursor.execute('''
            ALTER TABLE attendance_sessions 
            ADD COLUMN subject TEXT DEFAULT 'General'
        ''')

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

init_db()

class FaceRecognitionService:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.known_roll_numbers = []
        self.load_known_faces()
    
    def load_known_faces(self):
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
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        return face_locations
    
    def recognize_faces(self, frame):
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

face_service = FaceRecognitionService()

@app.route('/api/students', methods=['GET'])
def get_students():
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
    try:
        data = request.json
        print(f"Received data: {data.keys()}")
        
        name = data['name']
        roll_number = data['roll_number']
        image_data = data['image']  
        
        print(f"Processing student: {name}, {roll_number}")
        print(f"Image data length: {len(image_data)}")
        print(f"Image data starts with: {image_data[:50]}")
        
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
        
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img)
        
        if len(face_locations) == 0:
            print("No face detected in the image")
            return jsonify({'error': 'No face detected in the image'}), 400
        
        print(f"Found {len(face_locations)} face(s)")
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        encoding = face_encodings[0]
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, roll_number, encoding) VALUES (?, ?, ?)",
            (name, roll_number, json.dumps(encoding.tolist()))
        )
        conn.commit()
        conn.close()  
        print(f"Student {name} added successfully")
        face_service.load_known_faces()
        
        return jsonify({'message': 'Student added successfully'})
    
    except Exception as e:
        print(f"Error adding student: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan-id-card', methods=['POST'])
def scan_id_card():
    try:
        data = request.json
        image_data = data['image']
        
        print(f"Processing ID card image...")        
        if ',' in image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
        else:
            image_bytes = base64.b64decode(image_data)
            
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode ID card image")
            return jsonify({'error': 'Failed to decode image'}), 400
            
        print(f"ID card image shape: {img.shape}")
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)        
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        text = pytesseract.image_to_string(thresh)
        print(f"Extracted text: {text}")        
        name = None
        roll_number = None
        
        roll_patterns = [
            r'Roll\s*No\.?\s*[:\s]*([A-Za-z0-9]+)',
            r'Roll\s*Number\s*[:\s]*([A-Za-z0-9]+)',
            r'ID\s*[:\s]*([A-Za-z0-9]+)',
            r'Reg\s*No\.?\s*[:\s]*([A-Za-z0-9]+)',
            r'([A-Za-z]{2,4}\d{2,6})',  
        ]
        
        name_patterns = [
            r'Name\s*[:\s]*([A-Za-z\s]+)',
            r'Student\s*Name\s*[:\s]*([A-Za-z\s]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]        
        for pattern in roll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                roll_number = match.group(1).strip()
                break
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                name = ' '.join(word.capitalize() for word in name.split())
                break
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not roll_number:
            for line in lines:
                if re.match(r'^[A-Za-z]{2,4}\d{2,8}$', line):
                    roll_number = line
                    break
        
        if not name:
            for line in lines:
                if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$', line):
                    name = line
                    break
        
        print(f"Extracted - Name: {name}, Roll Number: {roll_number}")
        
        return jsonify({
            'name': name,
            'roll_number': roll_number,
            'raw_text': text
        })
    
    except Exception as e:
        print(f"Error scanning ID card: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.json
        session_name = data['session_name']
        subject = data.get('subject', 'General')
        duration_hours = data.get('duration_hours', 1)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO attendance_sessions (session_name, subject, start_time, end_time, duration_hours, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            (session_name, subject, start_time, end_time, duration_hours, False)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'session_name': session_name,
            'subject': subject,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': duration_hours
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/deactivate-all', methods=['POST'])
def deactivate_all_sessions():
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE attendance_sessions SET is_active = 0")
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'All sessions deactivated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/start', methods=['POST'])
def start_session(session_id):
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE attendance_sessions SET is_active = 0")        
        cursor.execute("UPDATE attendance_sessions SET is_active = 1 WHERE id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Session started successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>/mark-attendance', methods=['POST'])
def mark_attendance(session_id):
    try:
        data = request.json
        recognized_students = data['recognized_students']
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()        
        cursor.execute("SELECT is_active FROM attendance_sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if not session or not session[0]:
            return jsonify({'error': 'Session is not active'}), 400
        
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
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()        
        cursor.execute("UPDATE attendance_sessions SET is_active = 0, end_time = ? WHERE id = ?", 
                      (datetime.now(), session_id))        
        cursor.execute("SELECT id FROM students")
        all_students = cursor.fetchall()
        
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
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()    
    cursor.execute("PRAGMA table_info(attendance_sessions)")
    columns = [column[1] for column in cursor.fetchall()]    
    cursor.execute("""
        SELECT id, session_name, subject, start_time, end_time, 
               duration_hours, is_active, created_at 
        FROM attendance_sessions 
        ORDER BY created_at DESC
    """)
    sessions = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': row[0],
        'session_name': row[1],
        'subject': row[2],
        'start_time': row[3],
        'end_time': row[4],
        'duration_hours': row[5],
        'is_active': bool(row[6]),
        'created_at': row[7]
    } for row in sessions])

@app.route('/api/attendance/<int:session_id>', methods=['GET'])
def get_attendance(session_id):
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

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    subjects = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': row[0],
        'name': row[1],
        'created_at': row[2]
    } for row in subjects])

@app.route('/api/subjects', methods=['POST'])
def add_subject():
    try:
        data = request.json
        subject_name = data['name']       
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
        subject_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': subject_id,
            'name': subject_name,
            'message': 'Subject added successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()        
        cursor.execute("SELECT COUNT(*) FROM attendance_sessions WHERE subject = (SELECT name FROM subjects WHERE id = ?)", (subject_id,))
        session_count = cursor.fetchone()[0]
        
        if session_count > 0:
            return jsonify({'error': 'Cannot delete subject - it is being used in attendance sessions'}), 400
        
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Subject deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recognize-faces', methods=['POST'])
def recognize_faces():
    try:
        data = request.json
        image_data = data['image']
        session_id = data.get('session_id')
        
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
        recognized_students = face_service.recognize_faces(img)
        
        return jsonify({'recognized_students': recognized_students})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/monthly', methods=['GET'])
def get_monthly_report():
    try:
        month = request.args.get('month')
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400        
        year, month_num = map(int, month.split('-'))
        
        num_days = calendar.monthrange(year, month_num)[1]
        days = [f"{year}-{month_num:02d}-{day:02d}" for day in range(1, num_days + 1)]
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_number FROM students ORDER BY roll_number")
        students = cursor.fetchall()

        report_data = {
            'days': [day.split('-')[2] for day in days], 
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
    try:
        month = request.args.get('month')
        subject = request.args.get('subject', 'All')
        
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400        
        year, month_num = map(int, month.split('-'))
        
        num_days = calendar.monthrange(year, month_num)[1]
        days = [f"{year}-{month_num:02d}-{day:02d}" for day in range(1, num_days + 1)]
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, roll_number FROM students ORDER BY roll_number")
        students = cursor.fetchall()
        
        excel_data = []
        headers = ['Roll Number', 'Name'] + [f"Day {day}" for day in range(1, num_days + 1)] + ['Total Present', 'Percentage']
        excel_data.append(headers)
        
        for student_id, name, roll_number in students:
            row = [roll_number, name]
            total_present = 0
            
            for day in days:
                if subject == 'All':
                    cursor.execute('''
                        SELECT ar.status 
                        FROM attendance_records ar
                        JOIN attendance_sessions s ON ar.session_id = s.id
                        WHERE ar.student_id = ? AND DATE(s.start_time) = ?
                    ''', (student_id, day))
                else:
                    cursor.execute('''
                        SELECT ar.status 
                        FROM attendance_records ar
                        JOIN attendance_sessions s ON ar.session_id = s.id
                        WHERE ar.student_id = ? AND DATE(s.start_time) = ? AND s.subject = ?
                    ''', (student_id, day, subject))
                
                records = cursor.fetchall()
                
                if records:
                    if any(record[0] == 'present' for record in records):
                        row.append('P')
                        total_present += 1
                    else:
                        row.append('A')
                else:
                    row.append('-')            
            percentage = (total_present / num_days * 100) if num_days > 0 else 0
            row.extend([total_present, f"{percentage:.1f}%"])
            excel_data.append(row)
        
        conn.close()
        
        df = pd.DataFrame(excel_data[1:], columns=excel_data[0])
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        if subject == 'All':
            filename = f'attendance_report_{month}.xlsx'
        else:
            filename = f'attendance_report_{subject}_{month}.xlsx'
        
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-database', methods=['POST'])
def reset_database():
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS attendance_records")
        cursor.execute("DROP TABLE IF EXISTS attendance_sessions")
        cursor.execute("DROP TABLE IF EXISTS students")
        cursor.execute("DROP TABLE IF EXISTS subjects")
        
        conn.commit()
        conn.close()
        
        init_db()
        
        return jsonify({'message': 'Database reset successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/subject-excel', methods=['GET'])
def download_subject_excel_reports():
    try:
        month = request.args.get('month')
        if not month:
            return jsonify({'error': 'Month parameter is required'}), 400

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT subject FROM attendance_sessions ORDER BY subject")
        subjects = [row[0] for row in cursor.fetchall()]
        
        if not subjects:
            return jsonify({'error': 'No subjects found'}), 404
        
        import zipfile
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for subject in subjects:
                year, month_num = map(int, month.split('-'))                
                num_days = calendar.monthrange(year, month_num)[1]
                days = [f"{year}-{month_num:02d}-{day:02d}" for day in range(1, num_days + 1)]                
                cursor.execute("SELECT id, name, roll_number FROM students ORDER BY roll_number")
                students = cursor.fetchall()
                
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
                            WHERE ar.student_id = ? AND DATE(s.start_time) = ? AND s.subject = ?
                        ''', (student_id, day, subject))
                        
                        records = cursor.fetchall()
                        
                        if records:
                            if any(record[0] == 'present' for record in records):
                                row.append('P')
                                total_present += 1
                            else:
                                row.append('A')
                        else:
                            row.append('-')
                    
                    percentage = (total_present / num_days * 100) if num_days > 0 else 0
                    row.extend([total_present, f"{percentage:.1f}%"])
                    excel_data.append(row)                

                df = pd.DataFrame(excel_data[1:], columns=excel_data[0])
                subject_excel_buffer = BytesIO()
                df.to_excel(subject_excel_buffer, index=False, engine='openpyxl')
                subject_excel_buffer.seek(0)
                filename = f'attendance_report_{subject}_{month}.xlsx'
                zip_file.writestr(filename, subject_excel_buffer.getvalue())
        
        conn.close()
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'attendance_reports_all_subjects_{month}.zip',
            mimetype='application/zip'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_frontend():
    return send_file('../frontend/index.html')

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance_records WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()
        face_service.load_known_faces()
        
        return jsonify({'message': 'Student deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)