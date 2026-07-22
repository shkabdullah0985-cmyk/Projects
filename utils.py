import re
import pytz
from datetime import datetime, date, timedelta
import pymysql
from pymysql.cursors import DictCursor
from openpyxl import Workbook
from openpyxl.chart import PieChart, Reference, BarChart
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
import os
from config import Config

def get_db_connection():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset='utf8mb4',
        cursorclass=DictCursor
    )

def generate_student_id(cursor):
    cursor.execute("SELECT student_id FROM registrations ORDER BY id DESC LIMIT 1")
    last = cursor.fetchone()
    if not last:
        return 'A1'
    last_id = last['student_id']
    match = re.match(r'([A-Z])(\d+)', last_id)
    if not match:
        return 'A1'
    letter = match.group(1)
    num = int(match.group(2))
    if num < 10:
        return f'{letter}{num+1}'
    else:
        if letter == 'Z':
            return None
        next_letter = chr(ord(letter) + 1)
        return f'{next_letter}1'

def get_attendance_status(time_str):
    t = datetime.strptime(time_str, '%H:%M:%S').time()
    eight = datetime.strptime('08:00:00', '%H:%M:%S').time()
    nine = datetime.strptime('09:00:00', '%H:%M:%S').time()
    twelve = datetime.strptime('12:00:00', '%H:%M:%S').time()
    if t < eight:
        return 'NotStarted'
    elif eight <= t < nine:
        return 'Present'
    elif nine <= t < twelve:
        return 'Late'
    else:
        return 'Timeout'

def mark_absent_for_day(target_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id FROM registrations")
    students = cursor.fetchall()
    for row in students:
        sid = row['student_id']
        cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (sid, target_date))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
                (sid, target_date, datetime.min.time(), 'Absent')
            )
    conn.commit()
    cursor.close()
    conn.close()