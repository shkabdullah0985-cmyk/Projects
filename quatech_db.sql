CREATE DATABASE IF NOT EXISTS quastech_db; 
USE quastech_db;

-- Drop old tables and recreate
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS registrations;

CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(10) NOT NULL UNIQUE,
    year ENUM('FYBCA','SYBCA','TYBCA') NOT NULL,
    course VARCHAR(50) DEFAULT 'BCA',
    password VARCHAR(255) NOT NULL,  -- hashed password
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Select * from registrations;

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    time_in TIME NOT NULL,
    status ENUM('Present','Late','Absent','Timeout') NOT NULL,
    device_fingerprint VARCHAR(64),
    FOREIGN KEY (registration_number) REFERENCES registrations(registration_number) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (registration_number, date)
);

Select * from  attendance;

-- Admin table (for admin panel)
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
 Select * from admin;
 
-- Insert default admin (password: admin123)
INSERT INTO admin (username, password) VALUES ('admin', '$2b$12$KxQxJxQxJxQxJxQxJxQxJxQxJxQxJx');