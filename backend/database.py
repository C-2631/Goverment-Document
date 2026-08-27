import os
import sqlite3

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
if os.getenv("VERCEL"):
    SQLITE_DB_PATH = "/tmp/chatbot_pdf.db"
else:
    SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot_pdf.db")


def is_postgres():
    return bool(DATABASE_URL and PSYCOPG2_AVAILABLE)


def get_db():
    if is_postgres():
        # Handle postgresql:// vs postgres://
        db_url = DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    if is_postgres():
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_api_key TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS form_data (
            session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
            applicant_name TEXT DEFAULT '',
            address TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            date TEXT DEFAULT '',
            to_officer TEXT DEFAULT '',
            office_village TEXT DEFAULT '',
            subject_moje TEXT DEFAULT '',
            subject_taluko TEXT DEFAULT '',
            subject_jillo TEXT DEFAULT '',
            subject_survey_no TEXT DEFAULT '',
            body_name TEXT DEFAULT '',
            body_moje TEXT DEFAULT '',
            body_taluko TEXT DEFAULT '',
            body_jillo TEXT DEFAULT '',
            body_survey_no TEXT DEFAULT '',
            copy_details TEXT DEFAULT '',
            copy_quantity TEXT DEFAULT '',
            mtr_no TEXT DEFAULT '',
            online_app_no TEXT DEFAULT '',
            surveyor_name TEXT DEFAULT '',
            measurement_date TEXT DEFAULT '',
            deposit_fee TEXT DEFAULT '',
            behalf_name TEXT DEFAULT '',
            signature_path TEXT DEFAULT ''
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id BIGSERIAL PRIMARY KEY,
            session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
            sender TEXT,
            message TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        conn.close()
        print("Supabase (PostgreSQL) database initialized successfully.")
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_api_key TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_api_key TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS form_data (
            session_id TEXT PRIMARY KEY,
            applicant_name TEXT DEFAULT '',
            address TEXT DEFAULT '',
            mobile TEXT DEFAULT '',
            date TEXT DEFAULT '',
            to_officer TEXT DEFAULT '',
            office_village TEXT DEFAULT '',
            subject_moje TEXT DEFAULT '',
            subject_taluko TEXT DEFAULT '',
            subject_jillo TEXT DEFAULT '',
            subject_survey_no TEXT DEFAULT '',
            body_name TEXT DEFAULT '',
            body_moje TEXT DEFAULT '',
            body_taluko TEXT DEFAULT '',
            body_jillo TEXT DEFAULT '',
            body_survey_no TEXT DEFAULT '',
            copy_details TEXT DEFAULT '',
            copy_quantity TEXT DEFAULT '',
            mtr_no TEXT DEFAULT '',
            online_app_no TEXT DEFAULT '',
            surveyor_name TEXT DEFAULT '',
            measurement_date TEXT DEFAULT '',
            deposit_fee TEXT DEFAULT '',
            behalf_name TEXT DEFAULT '',
            signature_path TEXT DEFAULT '',
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender TEXT,
            message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        );
        """)
        conn.commit()
        conn.close()
        print("Local SQLite database initialized successfully.")


def create_session(session_id: str, user_api_key: str):
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    
    if is_postgres():
        cursor.execute(
            f"INSERT INTO sessions (session_id, user_api_key) VALUES ({ph}, {ph}) ON CONFLICT (session_id) DO NOTHING",
            (session_id, user_api_key)
        )
        cursor.execute(
            f"INSERT INTO form_data (session_id) VALUES ({ph}) ON CONFLICT (session_id) DO NOTHING",
            (session_id,)
        )
    else:
        cursor.execute(
            f"INSERT OR IGNORE INTO sessions (session_id, user_api_key) VALUES ({ph}, {ph})",
            (session_id, user_api_key)
        )
        cursor.execute(
            f"INSERT OR IGNORE INTO form_data (session_id) VALUES ({ph})",
            (session_id,)
        )
    conn.commit()
    conn.close()


def get_session_by_api_key(user_api_key: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(f"SELECT * FROM sessions WHERE user_api_key = {ph}", (user_api_key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}


def get_form_data(session_id: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(f"SELECT * FROM form_data WHERE session_id = {ph}", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}


def update_form_data(session_id: str, data: dict):
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"

    schema_cols = [
        "applicant_name", "address", "mobile", "date", "to_officer", "office_village",
        "subject_moje", "subject_taluko", "subject_jillo", "subject_survey_no",
        "body_name", "body_moje", "body_taluko", "body_jillo", "body_survey_no",
        "copy_details", "copy_quantity", "mtr_no", "online_app_no",
        "surveyor_name", "measurement_date", "deposit_fee", "behalf_name", "signature_path"
    ]

    update_pairs = []
    values = []
    for k, v in data.items():
        if k in schema_cols:
            update_pairs.append(f"{k} = {ph}")
            values.append(v)

    if not update_pairs:
        conn.close()
        return

    values.append(session_id)
    query = f"UPDATE form_data SET {', '.join(update_pairs)} WHERE session_id = {ph}"
    cursor.execute(query, tuple(values))

    # Update timestamp
    cursor.execute(
        f"UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = {ph}",
        (session_id,)
    )

    conn.commit()
    conn.close()


def get_chat_history(session_id: str) -> list:
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(
        f"SELECT sender, message, timestamp FROM chat_history WHERE session_id = {ph} ORDER BY id ASC",
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_chat_message(session_id: str, sender: str, message: str):
    conn = get_db()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(
        f"INSERT INTO chat_history (session_id, sender, message) VALUES ({ph}, {ph}, {ph})",
        (session_id, sender, message)
    )
    conn.commit()
    conn.close()
