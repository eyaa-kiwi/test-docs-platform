"""
SQLite 數據庫管理器
負責創建數據庫、管理 Sessions 和 Actions
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional
import config


def init_db() -> str:
    """初始化數據庫，創建必要的表格"""
    os.makedirs(config.STORAGE_DIR, exist_ok=True)

    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                status TEXT DEFAULT 'running'
            )
        """)

        # 只加 video_path 欄位（如果不存在 - 兼容舊數據庫）
        cursor.execute("PRAGMA table_info(sessions)")
        session_columns = [col[1] for col in cursor.fetchall()]
        if "video_path" not in session_columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN video_path TEXT DEFAULT ''")

        # 只加 element_id 欄位（如果不存在）
        cursor.execute("PRAGMA table_info(actions)")
        columns = [col[1] for col in cursor.fetchall()]
        if "element_id" not in columns:
            cursor.execute("ALTER TABLE actions ADD COLUMN element_id TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                selector TEXT,
                value TEXT,
                screenshot_path TEXT,
                purpose TEXT,
                page_title TEXT,
                page_url TEXT,
                element_name TEXT,
                element_type TEXT,
                element_id TEXT DEFAULT '',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_session
            ON actions(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_timestamp
            ON actions(timestamp)
        """)

    return config.DB_PATH


def create_session(name: str, url: str) -> int:
    """創建新的測試 session"""
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (name, url, started_at, status)
            VALUES (?, ?, ?, ?)
        """, (name, url, datetime.now().isoformat(), 'running'))

        return cursor.lastrowid


def end_session(session_id: int) -> bool:
    """結束測試 session"""
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET ended_at = ?, status = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), 'completed', session_id))

        return cursor.rowcount > 0


def update_session_video(session_id: int, video_path: str) -> bool:
    """更新 session 的影片路徑"""
    try:
        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET video_path = ? WHERE id = ?
            """, (video_path, session_id))
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"  ⚠️ DB error: {e}")
        return False


def record_action(
    session_id: int,
    action_type: str,
    selector: Optional[str] = None,
    value: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    purpose: Optional[str] = None,
    page_title: Optional[str] = None,
    page_url: Optional[str] = None,
    element_name: Optional[str] = None,
    element_type: Optional[str] = None,
    element_id: Optional[str] = None,
) -> bool:
    """記錄單次操作"""
    # 輸入驗證
    if action_type and len(action_type) > 50:
        action_type = action_type[:50]
    if selector and len(selector) > 500:
        selector = selector[:500]
    if value and len(value) > 2000:
        value = value[:2000]
    if purpose and len(purpose) > 1000:
        purpose = purpose[:1000]
    if page_title and len(page_title) > 500:
        page_title = page_title[:500]
    if page_url and len(page_url) > 2000:
        page_url = page_url[:2000]
    if element_name and len(element_name) > 500:
        element_name = element_name[:500]
    if element_type and len(element_type) > 100:
        element_type = element_type[:100]
    if element_id and len(element_id) > 200:
        element_id = element_id[:200]

    try:
        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO actions
                (session_id, timestamp, action_type, selector, value, screenshot_path, purpose,
                 page_title, page_url, element_name, element_type, element_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                datetime.now().isoformat(),
                action_type,
                selector,
                value,
                screenshot_path,
                purpose,
                page_title,
                page_url,
                element_name,
                element_type,
                element_id or '',
            ))
            return True
    except sqlite3.Error as e:
        print(f"  ⚠️ DB error: {e}")
        return False


def get_session(session_id: int) -> Optional[tuple]:
    """根據 session_id 獲取 session 詳情"""
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, url, started_at, ended_at, status, video_path
            FROM sessions
            WHERE id = ?
        """, (session_id,))
        return cursor.fetchone()


def get_session_actions(session_id: int) -> list:
    """獲取指定 session 的所有操作"""
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, action_type, selector, value, screenshot_path, purpose,
                   page_title, page_url, element_name, element_type, element_id
            FROM actions
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        return cursor.fetchall()


def get_all_sessions() -> list:
    """獲取所有 sessions"""
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, url, started_at, ended_at, status, video_path
            FROM sessions
            ORDER BY started_at DESC
        """)
        return cursor.fetchall()


if __name__ == "__main__":
    # 測試數據庫初始化
    db_path = init_db()
    print(f"數據庫已初始化：{db_path}")