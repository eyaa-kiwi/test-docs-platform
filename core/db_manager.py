"""
SQLite 數據庫管理器
負責創建數據庫、管理 Sessions 和 Actions
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional
import config


def init_db():
    """初始化數據庫，創建必要的表格"""
    os.makedirs(config.STORAGE_DIR, exist_ok=True)

    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    # 創建 sessions 表
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

    # 創建 actions 表
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
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # 創建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_actions_session
        ON actions(session_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_actions_timestamp
        ON actions(timestamp)
    """)

    conn.commit()
    conn.close()

    return config.DB_PATH


def create_session(name: str, url: str) -> int:
    """創建新的測試 session"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (name, url, started_at, status)
        VALUES (?, ?, ?, ?)
    """, (name, url, datetime.now().isoformat(), 'running'))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def end_session(session_id: int):
    """結束測試 session"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET ended_at = ?, status = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), 'completed', session_id))

    conn.commit()
    conn.close()


def record_action(
    session_id: int,
    action_type: str,
    selector: Optional[str] = None,
    value: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    purpose: Optional[str] = None
):
    """記錄單次操作"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO actions
        (session_id, timestamp, action_type, selector, value, screenshot_path, purpose)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        datetime.now().isoformat(),
        action_type,
        selector,
        value,
        screenshot_path,
        purpose
    ))

    conn.commit()
    conn.close()


def get_session_actions(session_id: int) -> list:
    """獲取指定 session 的所有操作"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, action_type, selector, value, screenshot_path, purpose
        FROM actions
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))

    actions = cursor.fetchall()
    conn.close()

    return actions


def get_all_sessions() -> list:
    """獲取所有 sessions"""
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, url, started_at, ended_at, status
        FROM sessions
        ORDER BY started_at DESC
    """)

    sessions = cursor.fetchall()
    conn.close()

    return sessions


if __name__ == "__main__":
    # 測試數據庫初始化
    db_path = init_db()
    print(f"數據庫已初始化：{db_path}")
