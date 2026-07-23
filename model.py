from utils import get_db_connection
from datetime import date

class Registration:
    @staticmethod
    def create(student_id, registration_number, name, mobile, year):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO registrations (student_id, registration_number, name, mobile, year) VALUES (%s, %s, %s, %s, %s)",
            (student_id, registration_number, name, mobile, year)
        )
        conn.commit()
        cursor.close()
        conn.close()
    
    @staticmethod
    def find_by_mobile(mobile):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations WHERE mobile = %s", (mobile,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    
    @staticmethod
    def find_by_registration_number(reg_number):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations WHERE registration_number = %s", (reg_number,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    
    @staticmethod
    def find_by_student_id(sid):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations WHERE student_id = %s", (sid,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result

class Attendance:
    @staticmethod
    def mark_attendance(student_id, time_in, status):
        conn = get_db_connection()
        cursor = conn.cursor()
        today = date.today()
        cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (student_id, today))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time_in, status) VALUES (%s, %s, %s, %s)",
            (student_id, today, time_in, status)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True