CREATE DATABASE IF NOT EXISTS quastech_db; 
USE quastech_db;

CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10) UNIQUE NOT NULL,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(10) NOT NULL UNIQUE,
    year ENUM('FYBCA','SYBCA','TYBCA') NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    time_in TIME NOT NULL,
    status ENUM('Present','Late','Absent','Timeout') NOT NULL,
    UNIQUE KEY unique_attendance (student_id, date),
    FOREIGN KEY (student_id) REFERENCES registrations(student_id)
);

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Insert default admin (password = '1246' hashed with bcrypt)
-- For simplicity, we'll use plain text (but we'll implement bcrypt in the app)
-- We'll handle this in the app initialization.