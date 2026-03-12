import sqlite3
import hashlib
import random
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Any

DB_NAME = "vacation_planner.db"
# В продакшене соль должна храниться в переменных окружения
SALT = os.getenv("APP_SALT", "change_me_in_prod_v1")

def get_connection() -> sqlite3.Connection:
    """Создает подключение к базе данных с поддержкой доступа по имени колонок."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = 1")
    return conn

def hash_password(password: str) -> str:
    """Хеширует пароль с использованием SHA-256 и соли."""
    salted = f"{password}{SALT}".encode('utf-8')
    return hashlib.sha256(salted).hexdigest()

def init_db() -> None:
    """Инициализирует схему базы данных и наполняет её демо-данными при первом запуске."""
    schema = [
        '''CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            department_id INTEGER,
            position_id INTEGER,
            total_vacation_days INTEGER DEFAULT 28,
            remaining_vacation_days INTEGER DEFAULT 28,
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (position_id) REFERENCES positions (id)
        )''',
        '''CREATE TABLE IF NOT EXISTS vacations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            comment TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )'''
    ]

    with get_connection() as conn:
        cursor = conn.cursor()
        for statement in schema:
            cursor.execute(statement)
        
        cursor.execute("SELECT count(*) as cnt FROM users")
        if cursor.fetchone()['cnt'] == 0:
            _seed_demo_data(cursor)
            conn.commit()

def _seed_demo_data(cursor: sqlite3.Cursor) -> None:
    """Наполняет базу начальными данными для демонстрации."""
    departments = [
        'Администрация', 'IT отдел', 'Бухгалтерия', 'Отдел продаж', 'HR',
        'Маркетинг', 'Логистика', 'Юридический отдел'
    ]
    dept_map = {}
    for dept in departments:
        cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
        cursor.execute("SELECT id FROM departments WHERE name=?", (dept,))
        dept_map[dept] = cursor.fetchone()['id']

    positions = [
        'Генеральный директор', 'Разработчик', 'Бухгалтер', 'Менеджер', 'HR-специалист',
        'Маркетолог', 'Юрист', 'Системный администратор'
    ]
    pos_map = {}
    for pos in positions:
        cursor.execute("INSERT OR IGNORE INTO positions (title) VALUES (?)", (pos,))
        cursor.execute("SELECT id FROM positions WHERE title=?", (pos,))
        pos_map[pos] = cursor.fetchone()['id']

    # Основные пользователи для входа
    base_users = [
        ('admin', 'admin123', 'hr', 'Администратор Системы', 'HR', 'HR-специалист'),
        ('manager', 'manager123', 'manager', 'Петр Руководитель', 'IT отдел', 'Генеральный директор'),
        ('user', 'user123', 'employee', 'Иван Разработчик', 'IT отдел', 'Разработчик'),
    ]

    for login, pwd, role, name, dept, pos in base_users:
        cursor.execute(
            'INSERT INTO users (username, password_hash, role, full_name, department_id, position_id) VALUES (?, ?, ?, ?, ?, ?)',
            (login, hash_password(pwd), role, name, dept_map[dept], pos_map[pos])
        )

    # Генерация массовки
    first_names = ["Александр", "Мария", "Дмитрий", "Елена", "Сергей", "Ольга", "Андрей", "Анна"]
    last_names = ["Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов"]
    
    for i in range(15):
        full_name = f"{random.choice(last_names)} {random.choice(first_names)}"
        username = f"user{i+1}"
        role = random.choice(['employee', 'manager'])
        dept_id = random.choice(list(dept_map.values()))
        pos_id = random.choice(list(pos_map.values()))
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, role, full_name, department_id, position_id) VALUES (?, ?, ?, ?, ?, ?)',
                (username, hash_password('123'), role, full_name, dept_id, pos_id)
            )
        except sqlite3.IntegrityError:
            continue

def get_departments() -> List[Tuple[int, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM departments ORDER BY name")
        return [(row['id'], row['name']) for row in cursor.fetchall()]

def get_positions() -> List[Tuple[int, str]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM positions ORDER BY title")
        return [(row['id'], row['title']) for row in cursor.fetchall()]

def create_user(username, password, role, full_name, dept_id, pos_id) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                'INSERT INTO users (username, password_hash, role, full_name, department_id, position_id) VALUES (?, ?, ?, ?, ?, ?)',
                (username, hash_password(password), role, full_name, dept_id, pos_id)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def get_all_users_with_details() -> List[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.full_name, u.username, u.role, d.name as dept_name, p.title as pos_title
            FROM users u
            LEFT JOIN departments d ON u.department_id = d.id
            LEFT JOIN positions p ON u.position_id = p.id
            ORDER BY u.full_name
        ''')
        return cursor.fetchall()

def update_user(user_id, full_name, role, department_id, position_id) -> None:
    with get_connection() as conn:
        conn.execute('''
            UPDATE users SET full_name = ?, role = ?, department_id = ?, position_id = ?
            WHERE id = ?
        ''', (full_name, role, department_id, position_id, user_id))
        conn.commit()

def delete_user(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

if __name__ == "__main__":
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME) # Для чистого теста при прямом запуске
    init_db()
    print("Database initialized successfully.")
