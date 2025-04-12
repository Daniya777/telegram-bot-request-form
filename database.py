import sqlite3

DB_NAME = "requests.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            bot_name TEXT,
            purpose TEXT,
            functions TEXT,
            admin_panel TEXT,
            buttons TEXT,
            data_storage TEXT,
            notifications TEXT,
            payment TEXT,
            business_info TEXT,
            urgency TEXT,
            other TEXT,
            admin_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_full_request(
    name, contact, bot_name, purpose, functions,
    admin_panel, buttons, data_storage, notifications,
    payment, business_info, urgency, other, admin_message_id
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bot_requests (
            name, contact, bot_name, purpose, functions,
            admin_panel, buttons, data_storage, notifications,
            payment, business_info, urgency, other, admin_message_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, contact, bot_name, purpose, functions,
        admin_panel, buttons, data_storage, notifications,
        payment, business_info, urgency, other, admin_message_id
    ))
    conn.commit()
    request_id = cursor.lastrowid
    conn.close()
    return request_id

def delete_request_by_id(request_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bot_requests WHERE id = ?", (request_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_admin_message_id(request_id: int) -> int | None:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT admin_message_id FROM bot_requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
