"""
SQLite 数据库管理 - 对话历史存储
"""
import sqlite3
import json
import uuid
import os
import threading
from datetime import datetime
from typing import Optional

# 数据库文件路径（项目根目录）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chat_history.db")

# 线程本地存储，确保每个线程使用独立连接
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接"""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """初始化数据库表结构"""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id          TEXT PRIMARY KEY,
            username    TEXT NOT NULL,
            title       TEXT NOT NULL DEFAULT '新对话',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_username
            ON chat_sessions(username);

        CREATE INDEX IF NOT EXISTS idx_sessions_updated
            ON chat_sessions(username, updated_at DESC);

        CREATE TABLE IF NOT EXISTS chat_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL DEFAULT '',
            time        TEXT NOT NULL,
            attachments TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON chat_messages(session_id);
    """)
    conn.commit()


# ========== 会话操作 ==========

def create_session(username: str, title: str = "新对话") -> dict:
    """创建新会话"""
    conn = get_connection()
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        "INSERT INTO chat_sessions (id, username, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, username, title, now, now)
    )
    conn.commit()
    return {"id": session_id, "title": title, "created_at": now}


def get_user_sessions(username: str) -> list:
    """获取用户所有会话列表（按更新时间倒序）"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.id, s.title, s.created_at, s.updated_at,
                  (SELECT COUNT(*) FROM chat_messages m WHERE m.session_id = s.id) AS message_count
           FROM chat_sessions s
           WHERE s.username = ?
           ORDER BY s.updated_at DESC""",
        (username,)
    ).fetchall()

    return [
        {
            "id": r["id"],
            "title": r["title"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "message_count": r["message_count"]
        }
        for r in rows
    ]


def get_session(username: str, session_id: str) -> Optional[dict]:
    """获取某个会话的详细信息和全部消息"""
    conn = get_connection()
    session_row = conn.execute(
        "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ? AND username = ?",
        (session_id, username)
    ).fetchone()

    if not session_row:
        return None

    msg_rows = conn.execute(
        "SELECT role, content, time, attachments FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()

    messages = []
    for m in msg_rows:
        try:
            attachments = json.loads(m["attachments"])
        except (json.JSONDecodeError, TypeError):
            attachments = []
        messages.append({
            "role": m["role"],
            "content": m["content"],
            "time": m["time"],
            "attachments": attachments
        })

    return {
        "id": session_row["id"],
        "title": session_row["title"],
        "created_at": session_row["created_at"],
        "updated_at": session_row["updated_at"],
        "messages": messages
    }


def add_messages(username: str, session_id: str, messages: list) -> dict:
    """向会话添加消息，自动创建会话（如不存在），自动更新标题"""
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 检查会话是否存在，不存在则自动创建
    existing = conn.execute(
        "SELECT id, title FROM chat_sessions WHERE id = ? AND username = ?",
        (session_id, username)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO chat_sessions (id, username, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, username, "新对话", now, now)
        )
        current_title = "新对话"
    else:
        current_title = existing["title"]

    # 插入消息
    for msg in messages:
        attachments_json = json.dumps(msg.get("attachments", []), ensure_ascii=False)
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, time, attachments) VALUES (?, ?, ?, ?, ?)",
            (session_id, msg.get("role", "user"), msg.get("content", ""), msg.get("time", now), attachments_json)
        )

    # 自动用第一条用户消息作为标题
    if current_title == "新对话":
        first_user_msg = conn.execute(
            "SELECT content FROM chat_messages WHERE session_id = ? AND role = 'user' AND content != '' ORDER BY id ASC LIMIT 1",
            (session_id,)
        ).fetchone()
        if first_user_msg:
            title_text = first_user_msg["content"].strip()
            current_title = title_text[:20] + ("..." if len(title_text) > 20 else "")
            conn.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (current_title, session_id))

    # 更新 updated_at
    conn.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    conn.commit()

    return {"success": True, "title": current_title}


def update_session_title(username: str, session_id: str, title: str) -> bool:
    """更新会话标题"""
    conn = get_connection()
    result = conn.execute(
        "UPDATE chat_sessions SET title = ? WHERE id = ? AND username = ?",
        (title, session_id, username)
    )
    conn.commit()
    return result.rowcount > 0


def delete_session(username: str, session_id: str) -> bool:
    """删除会话（级联删除消息）"""
    conn = get_connection()
    result = conn.execute(
        "DELETE FROM chat_sessions WHERE id = ? AND username = ?",
        (session_id, username)
    )
    conn.commit()
    return result.rowcount > 0


# 启动时初始化数据库
init_db()
