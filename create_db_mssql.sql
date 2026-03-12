-- Скрипт создания БД для MS SQL Server
-- Проект: VacationPlanner

CREATE TABLE departments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE positions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(20) NOT NULL, -- 'employee', 'manager', 'hr'
    full_name NVARCHAR(100) NOT NULL,
    department_id INT,
    position_id INT,
    total_vacation_days INT DEFAULT 28,
    remaining_vacation_days INT DEFAULT 28,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

CREATE TABLE vacations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    comment NVARCHAR(MAX),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
