import os
import re
import math
from datetime import datetime, date, time, timedelta
from io import BytesIO
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
import pymysql
from pymysql.cursors import DictCursor
import pytz
from openpyxl import Workbook
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '@bdullah1266',   # CHANGE to your MySQL password
    'database': 'quastech_db',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'autocommit': True
}

# College GPS coordinates (replace with your actual values)
COLLEGE_LAT = 19.148643
COLLEGE_LON = 73.036216
GPS_RADIUS_METERS = 200

IST = pytz.timezone('Asia/Kolkata')

def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# --- Haversine Distance ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- Student ID Generation ---
def generate_next_student_id():
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id FROM registrations ORDER BY student_id")
            rows = cur.fetchall()
            existing_ids = [row['student_id'] for row in rows]
            if not existing_ids:
                return 'A1'
            last = existing_ids[-1]
            match = re.match(r'([A-Z])(\d+)', last)
            if not match:
                return 'A1'
            letter, num = match.groups()
            num = int(num)
            if num < 10:
                next_id = f"{letter}{num+1}"
                if next_id not in existing_ids:
                    return next_id
            possible = []
            for l in range(ord('A'), ord('Z')+1):
                for n in range(1, 11):
                    possible.append(f"{chr(l)}{n}")
            for pid in possible:
                if pid not in existing_ids:
                    return pid
            return None
    finally:
        conn.close()

# --- Auto-Absent (6:01 PM IST) ---
def mark_absent_students():
    today = datetime.now(IST).date()
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id FROM registrations")
            all_students = [row['student_id'] for row in cur.fetchall()]
            cur.execute("SELECT student_id FROM attendance WHERE date = %s", (today,))
            present_today = [row['student_id'] for row in cur.fetchall()]
            absent_students = set(all_students) - set(present_today)
            now_time = datetime.now(IST).time()
            for sid in absent_students:
                cur.execute(
                    "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
                    (sid, today, now_time, 'Absent')
                )
            conn.commit()
            print(f"✅ Marked {len(absent_students)} students as Absent for {today}")
    except Exception as e:
        print(f"❌ Auto-absent error: {e}")
    finally:
        conn.close()

# --- Helper: Convert timedelta to HH:MM:SS string ---
def timedelta_to_str(td):
    if td is None:
        return ''
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return str(td)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '1246':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin.html', error="Wrong password")
    if not session.get('admin_logged_in'):
        return render_template('admin.html', error=None)

    conn = get_db_connection()
    registrations = []
    attendance = []
    db_error = None
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM registrations ORDER BY student_id")
                registrations = cur.fetchall()
                cur.execute("""
                    SELECT a.student_id, r.registration_number, r.name, a.date, a.time_in, a.status
                    FROM attendance a
                    JOIN registrations r ON a.student_id = r.student_id
                    ORDER BY a.date DESC, a.student_id
                """)
                attendance = cur.fetchall()
                # Convert time_in (timedelta) to string for display
                for row in attendance:
                    if row.get('time_in'):
                        row['time_in'] = timedelta_to_str(row['time_in'])
        except pymysql.Error as e:
            db_error = str(e)
        finally:
            conn.close()
    else:
        db_error = "Could not connect to database."

    return render_template('admin.html', registrations=registrations, attendance=attendance, db_error=db_error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_panel'))

# --- API Endpoints ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    reg_num = data.get('registration_number', '').strip()
    mobile = data.get('mobile', '').strip()
    year = data.get('year', '').strip()

    if not all([name, reg_num, mobile, year]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
    if len(mobile) != 10 or not mobile.isdigit():
        return jsonify({'success': False, 'message': 'Mobile must be exactly 10 digits.'}), 400
    if year not in ['FYBCA', 'SYBCA', 'TYBCA']:
        return jsonify({'success': False, 'message': 'Invalid year.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id FROM registrations WHERE registration_number = %s", (reg_num,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Registration number already exists. Please use a unique registration number.'}), 400
            cur.execute("SELECT student_id FROM registrations WHERE mobile = %s", (mobile,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Mobile number already registered. Please use a different mobile number.'}), 400

            student_id = generate_next_student_id()
            if student_id is None:
                return jsonify({'success': False, 'message': 'Maximum student limit reached (Z10).'}), 400

            cur.execute(
                "INSERT INTO registrations (student_id, registration_number, name, mobile, year) VALUES (%s, %s, %s, %s, %s)",
                (student_id, reg_num, name, mobile, year)
            )
            conn.commit()
            return jsonify({'success': True, 'message': f'Registration successful! Your Student ID is: {student_id}.', 'student_id': student_id})
    except pymysql.IntegrityError as e:
        return jsonify({'success': False, 'message': 'Database error: ' + str(e)}), 400
    finally:
        conn.close()

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    student_id = data.get('student_id', '').strip().upper()
    year = data.get('year', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not student_id or not year:
        return jsonify({'success': False, 'message': 'Student ID and Year are required.'}), 400
    if year not in ['FYBCA', 'SYBCA', 'TYBCA']:
        return jsonify({'success': False, 'message': 'Invalid year.'}), 400
    if latitude is None or longitude is None:
        return jsonify({'success': False, 'message': 'Location access is required. Please enable GPS.'}), 400

    distance = haversine(COLLEGE_LAT, COLLEGE_LON, float(latitude), float(longitude))
    if distance > GPS_RADIUS_METERS:
        return jsonify({'success': False, 'message': f'You are not within college campus. Distance: {int(distance)} meters.'}), 400

    now = datetime.now(IST)
    current_time = now.time()
    current_date = now.date()

    if current_time < time(12, 0):
        return jsonify({'success': False, 'message': 'Attendance window starts at 12:00 PM IST.'}), 400
    if current_time >= time(18, 0):
        return jsonify({'success': False, 'message': 'Attendance window closed. Timeout.'}), 400

    status = 'Present' if current_time < time(13, 0) else 'Late'

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT student_id, year FROM registrations WHERE student_id = %s", (student_id,))
            student = cur.fetchone()
            if not student:
                return jsonify({'success': False, 'message': 'Invalid Student ID. Please register first.'}), 400
            if student['year'] != year:
                return jsonify({'success': False, 'message': f"Student is in {student['year']}, not {year}."}), 400

            cur.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (student_id, current_date))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Attendance already marked for today.'}), 400

            cur.execute(
                "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
                (student_id, current_date, current_time, status)
            )
            conn.commit()
            return jsonify({'success': True, 'message': f'Attendance marked as {status}.', 'status': status})
    finally:
        conn.close()

# ---- Download Full Report (4 Sheets) ----
@app.route('/download_full_report', methods=['GET'])
def download_full_report():
    from openpyxl.chart import BarChart, PieChart, Reference
    from openpyxl.styles import Alignment
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()

    # ---- Sheet 1: Registrations ----
    ws1 = wb.active
    ws1.title = "Registrations"
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT student_id, registration_number, name, mobile, year, registered_at FROM registrations ORDER BY student_id")
                regs = cur.fetchall()
                if regs:
                    ws1.append(['Student ID', 'Registration Number', 'Name', 'Mobile', 'Year', 'Registered At'])
                    for reg in regs:
                        ws1.append([
                            reg['student_id'],
                            reg['registration_number'],
                            reg['name'],
                            reg['mobile'],
                            reg['year'],
                            reg['registered_at'].strftime('%Y-%m-%d %H:%M:%S') if reg['registered_at'] else ''
                        ])
                else:
                    ws1.append(['No registrations found.'])
        finally:
            conn.close()

    # ---- Sheet 2: Attendance ----
    ws2 = wb.create_sheet("Attendance")
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.student_id, r.registration_number, r.name, a.date, a.time_in, a.status
                    FROM attendance a
                    JOIN registrations r ON a.student_id = r.student_id
                    ORDER BY a.date DESC, a.student_id
                """)
                atts = cur.fetchall()
                if atts:
                    ws2.append(['Student ID', 'Registration Number', 'Name', 'Date', 'Time In', 'Status'])
                    for att in atts:
                        # Convert timedelta to string for Excel
                        time_str = timedelta_to_str(att.get('time_in'))
                        ws2.append([
                            att['student_id'],
                            att['registration_number'],
                            att['name'],
                            att['date'].strftime('%Y-%m-%d') if att['date'] else '',
                            time_str,
                            att['status']
                        ])
                else:
                    ws2.append(['No attendance records found.'])
        finally:
            conn.close()

    # ---- Sheet 3: Overall Summary + Bar Chart ----
    ws3 = wb.create_sheet("Overall Summary")
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        r.student_id,
                        r.registration_number,
                        r.name,
                        SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS Present,
                        SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) AS Late,
                        SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS Absent,
                        SUM(CASE WHEN a.status = 'Timeout' THEN 1 ELSE 0 END) AS Timeout,
                        COUNT(a.id) AS Total_Days
                    FROM registrations r
                    LEFT JOIN attendance a ON r.student_id = a.student_id
                    GROUP BY r.student_id
                    ORDER BY r.student_id
                """)
                summary = cur.fetchall()
                if summary:
                    ws3.append(['Student ID', 'Registration Number', 'Name', 'Present', 'Late', 'Absent', 'Timeout', 'Total Days', 'Attendance %'])
                    for row in summary:
                        total = row['Total_Days']
                        att_percent = round((row['Present'] + row['Late']) / total * 100, 2) if total > 0 else 0
                        ws3.append([
                            row['student_id'],
                            row['registration_number'],
                            row['name'],
                            row['Present'],
                            row['Late'],
                            row['Absent'],
                            row['Timeout'],
                            total,
                            att_percent
                        ])

                    if len(summary) > 1:
                        bar_chart = BarChart()
                        bar_chart.title = "Overall Attendance Percentage per Student"
                        bar_chart.x_axis.title = "Student"
                        bar_chart.y_axis.title = "Percentage"
                        data = Reference(ws3, min_col=9, min_row=2, max_row=len(summary)+1)
                        categories = Reference(ws3, min_col=1, min_row=2, max_row=len(summary)+1)
                        bar_chart.add_data(data, titles_from_data=False)
                        bar_chart.set_categories(categories)
                        ws3.add_chart(bar_chart, "K2")
                else:
                    ws3.append(['No data available.'])
        finally:
            conn.close()

    # ---- Sheet 4: Student Slicer (Dropdown + Weekly %) ----
    ws4 = wb.create_sheet("Student Slicer")
    now = datetime.now(IST)
    current_month = now.month
    current_year = now.year
    conn = get_db_connection()
    data_rows = []
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.student_id, r.name, a.date, a.status,
                           DAY(a.date) as day_of_month
                    FROM attendance a
                    JOIN registrations r ON a.student_id = r.student_id
                    WHERE MONTH(a.date) = %s AND YEAR(a.date) = %s
                    ORDER BY a.student_id, a.date
                """, (current_month, current_year))
                records = cur.fetchall()
                student_weekly = {}
                for rec in records:
                    sid = rec['student_id']
                    name = rec['name']
                    day = rec['day_of_month']
                    if day <= 7:
                        week = 1
                    elif day <= 14:
                        week = 2
                    elif day <= 21:
                        week = 3
                    else:
                        week = 4
                    status = rec['status']
                    key = (sid, week)
                    if key not in student_weekly:
                        student_weekly[key] = {'Present':0, 'Late':0, 'Absent':0, 'Timeout':0, 'total_days':0, 'name':name}
                    student_weekly[key][status] += 1
                    student_weekly[key]['total_days'] += 1
                for (sid, week), counts in student_weekly.items():
                    total = counts['total_days']
                    perc = round((counts['Present'] + counts['Late']) / total * 100, 2) if total > 0 else 0
                    data_rows.append([
                        sid,
                        counts['name'],
                        week,
                        counts['Present'],
                        counts['Late'],
                        counts['Absent'],
                        counts['Timeout'],
                        total,
                        perc
                    ])
        finally:
            conn.close()

    wb.create_sheet("WeeklyData")
    ws_data = wb["WeeklyData"]
    ws_data.sheet_state = 'hidden'
    ws_data.append(['Student ID', 'Name', 'Week', 'Present', 'Late', 'Absent', 'Timeout', 'Total Days', 'Attendance %'])
    for row in data_rows:
        ws_data.append(row)

    ws4.title = "Student Slicer"
    student_names = sorted(set(row[1] for row in data_rows))
    if not student_names:
        ws4.append(['No data for this month.'])
    else:
        dv = DataValidation(type="list", formula1='"{}"'.format(','.join(student_names)))
        ws4.add_data_validation(dv)
        dv.add('B1')
        ws4['A1'] = "Select Student:"
        ws4['B1'] = student_names[0]

        ws4['A3'] = "Week"
        ws4['B3'] = "Attendance %"
        for i in range(1, 5):
            ws4.cell(row=3+i, column=1, value=f"Week {i}")
            ws4.cell(row=3+i, column=2).value = f'=SUMIFS(WeeklyData!I:I, WeeklyData!B:B, $B$1, WeeklyData!C:C, {i})'

        chart_data = Reference(ws4, min_col=2, min_row=4, max_row=7)
        categories = Reference(ws4, min_col=1, min_row=4, max_row=7)
        chart = BarChart()
        chart.title = "Weekly Attendance Percentage"
        chart.x_axis.title = "Week"
        chart.y_axis.title = "Percentage"
        chart.add_data(chart_data, titles_from_data=False)
        chart.set_categories(categories)
        ws4.add_chart(chart, "D3")

        for row in ws4.iter_rows(min_row=3, max_row=7, min_col=1, max_col=2):
            for cell in row:
                cell.alignment = Alignment(horizontal='center')

    file_bytes = BytesIO()
    wb.save(file_bytes)
    file_bytes.seek(0)
    filename = "full_attendance_report.xlsx"
    return send_file(
        file_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(
    mark_absent_students,
    'cron',
    hour=18,
    minute=1,
    timezone=IST
)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)