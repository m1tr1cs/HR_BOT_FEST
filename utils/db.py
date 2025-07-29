# utils/db.py

import sqlite3
import logging
from datetime import datetime

DB_PATH = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vacancies (
        vacancy_id INTEGER PRIMARY KEY,
        position TEXT,
        market TEXT,
        city TEXT,
        location TEXT,
        age_range TEXT,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        age TEXT,
        chat_id TEXT,
        vacancy_id INTEGER,
        job_description TEXT,
        created_at TEXT,
        check_feedback INTEGER DEFAULT 0,
        resume_link TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id TEXT PRIMARY KEY,
        name TEXT,
        phone TEXT,
        age TEXT,
        resume_link TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()
    logging.info("✅ SQLite база ініціалізована")


def get_vacancies():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vacancies")
        rows = cursor.fetchall()
        conn.close()

        keys = ["vacancy_id", "position", "market", "city", "location", "age_range", "description"]
        return [dict(zip(keys, row)) for row in rows]
    except Exception:
        logging.exception("❌ Помилка отримання вакансій з бази")
        return []


def save_candidate(name, phone, age, chat_id, vacancy, resume_link=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # створення user, якщо немає, і одразу пишемо всі поля!
        cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (str(chat_id),))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (chat_id, name, phone, age, resume_link, role) VALUES (?, ?, ?, ?, ?, ?)",
                (str(chat_id), name, phone, age, resume_link, "user")
            )
        else:
            # якщо є — оновити дані (щоб вони завжди були актуальні)
            cursor.execute(
                "UPDATE users SET name = ?, phone = ?, age = ?, resume_link = ? WHERE chat_id = ?",
                (name, phone, age, resume_link, str(chat_id))
            )

        job_description = f"{vacancy.get('position')} - {vacancy.get('market')} ({vacancy.get('location')})"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO candidates (name, phone, age, chat_id, vacancy_id, job_description, created_at, resume_link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, age, str(chat_id), vacancy.get("vacancy_id"), job_description, created_at, resume_link))

        conn.commit()
        conn.close()
        logging.info(f"📝 Збережено кандидата: {name} на вакансію: {job_description}")
    except Exception:
        logging.exception("❌ Помилка збереження кандидата")


def get_vacancies_for_age(age: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    if age < 18:
        cursor.execute("SELECT * FROM vacancies WHERE age_range = '16-17'")
    else:
        cursor.execute("SELECT * FROM vacancies WHERE age_range != '16-17'")

    rows = cursor.fetchall()
    conn.close()

    keys = ["vacancy_id", "position", "market", "city", "location", "age_range", "description"]
    return [dict(zip(keys, row)) for row in rows]


def get_candidate_by_chat_id(chat_id: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, phone, age FROM candidates
        WHERE chat_id = ?
        ORDER BY id DESC LIMIT 1
    """, (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"name": row[0], "phone": row[1], "age": row[2]}
    return None


def get_user_feedbacks(chat_id: int):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, job_description, created_at
        FROM candidates
        WHERE chat_id = ?
        ORDER BY created_at DESC
    """, (str(chat_id),))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_feedback(record_id: int, chat_id: int = None):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    if chat_id is not None:
        cursor.execute("DELETE FROM candidates WHERE id = ? AND chat_id = ?", (record_id, str(chat_id)))
    else:
        cursor.execute("DELETE FROM candidates WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def is_admin(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE chat_id = ?", (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 'admin'


def set_setting(key: str, value: str):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key: str):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_feedbacks():
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, phone, age, chat_id, job_description, created_at, check_feedback, resume_link
        FROM candidates
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_feedback_checked(record_id: int):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET check_feedback = 1 WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def get_all_cities():
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city FROM vacancies ORDER BY city")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


def get_markets_by_city(city: str):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT market FROM vacancies WHERE city = ? ORDER BY market", (city,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


def get_vacancies_by_market(city: str, market: str):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vacancy_id, position, location, age_range, description
        FROM vacancies
        WHERE city = ? AND market = ?
        ORDER BY position
    """, (city, market))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_vacancy(vacancy_id: int):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()

    # Видалити всіх кандидатів, що відгукнулись на цю вакансію
    # cursor.execute("DELETE FROM candidates WHERE vacancy_id = ?", (vacancy_id,))

    # Потім видалити саму вакансію
    cursor.execute("DELETE FROM vacancies WHERE vacancy_id = ?", (vacancy_id,))

    conn.commit()
    conn.close()


def update_vacancy(vacancy_id: int, position, market, city, location, age_range, description):
    conn = sqlite3.connect("bot.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vacancies
        SET position = ?, market = ?, city = ?, location = ?, age_range = ?, description = ?
        WHERE vacancy_id = ?
    """, (position, market, city, location, age_range, description, vacancy_id))
    conn.commit()
    conn.close()


def has_applied(chat_id: int, vacancy_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM candidates
        WHERE chat_id = ? AND vacancy_id = ? AND check_feedback = 0
        LIMIT 1
    """, (str(chat_id), vacancy_id))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def set_admin(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE chat_id = ?", (str(chat_id),))
    conn.commit()
    conn.close()


def get_chat_id_by_phone(phone: str):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM candidates WHERE phone = ? ORDER BY id DESC LIMIT 1", (phone,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def remove_admin(chat_id: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'user' WHERE chat_id = ?", (str(chat_id),))
    conn.commit()
    conn.close()


def has_feedback_for_vacancy(vacancy_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
            SELECT 1 FROM candidates WHERE vacancy_id = ? LIMIT 1
        """, (vacancy_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def add_vacancy(position, market, city, location, age_range, description):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vacancies (position, market, city, location, age_range, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (position, market, city, location, age_range, description))
    conn.commit()
    conn.close()


def hide_vacancy(vacancy_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE vacancies SET hidden = 1 WHERE vacancy_id = ?", (vacancy_id,))
    conn.commit()
    conn.close()


def get_vacancies_by_id(vacancy_id: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT position, market, city, location, age_range, description FROM vacancies WHERE vacancy_id = ?",
        (vacancy_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def update_resume_link(chat_id, resume_link):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET resume_link = ? WHERE chat_id = ?", (resume_link, chat_id))
    conn.commit()
    conn.close()


def get_resume_link(chat_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT resume_link FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_user_profile(chat_id: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, phone, age, role, resume_link FROM users WHERE chat_id = ?",
        (str(chat_id),)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "phone": row[1],
            "age": row[2],
            "role": row[3],
            "resume_link": row[4]
        }
    return None

def get_admin_chat_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users WHERE role = 'admin'")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_last_candidate_id_by_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM candidates WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
        (str(chat_id),)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
