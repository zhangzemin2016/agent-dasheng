"""
统一数据库管理模块
使用 SQLite 管理所有结构化数据
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from utils.logger import get_logger
from constants.builtin_paths import BuiltinPaths

logger = get_logger("storage.database")


def get_db_path() -> Path:
    """获取数据库路径"""
    db_dir = BuiltinPaths.DB_ROOT
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "myagent.db"


class Database:
    """SQLite 数据库管理类"""

    _instance: Optional['Database'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_path = get_db_path()
        self._init_tables()
        self._initialized = True
        logger.info(f"数据库初始化完成: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    project_path TEXT,
                    title TEXT NOT NULL,
                    summary TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # 消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # 执行上下文表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    project_path TEXT,
                    working_dir TEXT,
                    execution_history TEXT,
                    pending_confirmations TEXT,
                    current_plan_id TEXT,
                    current_step_index INTEGER DEFAULT 0,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # 计划表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    project_path TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    current_step_index INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
                )
            """)

            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_path)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_plans_session ON plans(session_id)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_plans_project ON plans(project_path)")


# ==================== 会话存储操作 ====================

class SessionRepository:
    """会话数据仓库"""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def save(self, session: Dict[str, Any]) -> bool:
        """保存会话"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # 保存会话基本信息
                cursor.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (id, project_path, title, summary, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session['id'],
                    session.get('project_path', ''),
                    session.get('title', '新对话'),
                    session.get('summary', ''),
                    session.get('created_at', time.time()),
                    session.get('updated_at', time.time())
                ))

                # 删除旧消息
                cursor.execute(
                    "DELETE FROM messages WHERE session_id = ?", (session['id'],))

                # 保存消息
                for msg in session.get('messages', []):
                    # 确保 msg 是字典格式
                    if not isinstance(msg, dict):
                        # 如果是 LangChain 消息对象，转换为字典
                        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
                        if isinstance(msg, HumanMessage):
                            msg = {'role': 'user', 'content': msg.content, 'timestamp': time.time()}
                        elif isinstance(msg, AIMessage):
                            msg = {'role': 'assistant', 'content': msg.content, 'timestamp': time.time()}
                        elif isinstance(msg, SystemMessage):
                            msg = {'role': 'system', 'content': msg.content, 'timestamp': time.time()}
                        elif isinstance(msg, ToolMessage):
                            msg = {'role': 'tool', 'content': msg.content, 'tool_call_id': msg.tool_call_id, 'timestamp': time.time()}
                        else:
                            logger.error(f"未知消息类型：{type(msg)}")
                            continue
                    
                    cursor.execute("""
                        INSERT INTO messages (session_id, role, content, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (
                        session['id'],
                        msg['role'],
                        msg['content'],
                        msg.get('timestamp', time.time())
                    ))

            logger.debug(f"会话已保存: {session['id'][:8]}")
            return True
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载单个会话"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # 加载会话
                cursor.execute(
                    "SELECT * FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                session = {
                    'id': row['id'],
                    'project_path': row['project_path'],
                    'title': row['title'],
                    'summary': row['summary'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'messages': []
                }

                # 加载消息
                cursor.execute("""
                    SELECT role, content, timestamp 
                    FROM messages 
                    WHERE session_id = ? 
                    ORDER BY timestamp
                """, (session_id,))

                for msg_row in cursor.fetchall():
                    session['messages'].append({
                        'role': msg_row['role'],
                        'content': msg_row['content'],
                        'timestamp': msg_row['timestamp']
                    })

                return session
        except Exception as e:
            logger.error(f"加载会话失败: {e}")
            return None

    def load_all(self, project_path: str = None) -> List[Dict[str, Any]]:
        """加载所有会话（可按项目筛选）"""
        sessions = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if project_path:
                    cursor.execute("""
                        SELECT id FROM sessions 
                        WHERE project_path = ? 
                        ORDER BY updated_at DESC
                    """, (project_path,))
                else:
                    cursor.execute(
                        "SELECT id FROM sessions ORDER BY updated_at DESC")

                for row in cursor.fetchall():
                    session = self.load(row['id'])
                    if session:
                        sessions.append(session)
        except Exception as e:
            logger.error(f"加载会话列表失败: {e}")

        return sessions

    def delete(self, session_id: str) -> bool:
        """删除会话"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM sessions WHERE id = ?", (session_id,))
            logger.info(f"会话已删除: {session_id[:8]}")
            return True
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    def update_summary(self, session_id: str, summary: str) -> bool:
        """更新会话摘要"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions SET summary = ?, updated_at = ?
                    WHERE id = ?
                """, (summary, time.time(), session_id))
            return True
        except Exception as e:
            logger.error(f"更新摘要失败: {e}")
            return False


# ==================== 执行上下文存储操作 ====================

class ContextRepository:
    """执行上下文数据仓库"""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def save(self, session_id: str, context_data: Dict[str, Any]) -> bool:
        """保存执行上下文"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO execution_context
                    (session_id, project_path, working_dir, execution_history,
                     pending_confirmations, current_plan_id, current_step_index, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    context_data.get('project_path'),
                    context_data.get('working_dir'),
                    json.dumps(context_data.get(
                        'execution_history', []), ensure_ascii=False),
                    json.dumps(context_data.get(
                        'pending_confirmations', []), ensure_ascii=False),
                    context_data.get('current_plan_id'),
                    context_data.get('current_step_index', 0),
                    time.time()
                ))
            logger.debug(f"上下文已保存: session={session_id[:8]}")
            return True
        except Exception as e:
            logger.error(f"保存上下文失败: {e}")
            return False

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载执行上下文"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM execution_context WHERE session_id = ?
                """, (session_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    'project_path': row['project_path'],
                    'working_dir': row['working_dir'],
                    'execution_history': json.loads(row['execution_history'] or '[]'),
                    'pending_confirmations': json.loads(row['pending_confirmations'] or '[]'),
                    'current_plan_id': row['current_plan_id'],
                    'current_step_index': row['current_step_index']
                }
        except Exception as e:
            logger.error(f"加载上下文失败: {e}")
            return None

    def delete(self, session_id: str) -> bool:
        """删除执行上下文"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM execution_context WHERE session_id = ?", (session_id,))
            return True
        except Exception as e:
            logger.error(f"删除上下文失败: {e}")
            return False


# ==================== 计划存储操作 ====================

class PlanRepository:
    """计划数据仓库"""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def save(self, plan: Dict[str, Any]) -> bool:
        """保存计划"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO plans
                    (id, session_id, project_path, name, description, status,
                     steps, current_step_index, created_at, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    plan['id'],
                    plan.get('session_id'),
                    plan.get('project_path'),
                    plan['name'],
                    plan.get('description', ''),
                    plan['status'],
                    json.dumps(plan['steps'], ensure_ascii=False),
                    plan.get('current_step_index', 0),
                    plan['created_at'],
                    plan.get('started_at'),
                    plan.get('completed_at')
                ))
            logger.debug(f"计划已保存: {plan['id'][:8]}")
            return True
        except Exception as e:
            logger.error(f"保存计划失败: {e}")
            return False

    def load(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """加载计划"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
                row = cursor.fetchone()

                if not row:
                    return None

                return {
                    'id': row['id'],
                    'session_id': row['session_id'],
                    'project_path': row['project_path'],
                    'name': row['name'],
                    'description': row['description'],
                    'status': row['status'],
                    'steps': json.loads(row['steps']),
                    'current_step_index': row['current_step_index'],
                    'created_at': row['created_at'],
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at']
                }
        except Exception as e:
            logger.error(f"加载计划失败: {e}")
            return None

    def list_all(self, project_path: str = None) -> List[Dict[str, Any]]:
        """列出所有计划"""
        plans = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if project_path:
                    cursor.execute("""
                        SELECT id, name, status, created_at, steps, current_step_index
                        FROM plans WHERE project_path = ?
                        ORDER BY created_at DESC
                    """, (project_path,))
                else:
                    cursor.execute("""
                        SELECT id, name, status, created_at, steps, current_step_index
                        FROM plans ORDER BY created_at DESC
                    """)

                for row in cursor.fetchall():
                    steps = json.loads(row['steps'])
                    completed = len(
                        [s for s in steps if s.get('status') == 'completed'])
                    plans.append({
                        'id': row['id'],
                        'name': row['name'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'progress': {
                            'total': len(steps),
                            'completed': completed
                        }
                    })
        except Exception as e:
            logger.error(f"列出计划失败: {e}")

        return plans

    def delete(self, plan_id: str) -> bool:
        """删除计划"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
            logger.info(f"计划已删除: {plan_id[:8]}")
            return True
        except Exception as e:
            logger.error(f"删除计划失败: {e}")
            return False


# ==================== 便捷访问函数 ====================

def get_database() -> Database:
    """获取数据库单例"""
    return Database()


def get_session_repository() -> SessionRepository:
    """获取会话仓库"""
    return SessionRepository()


def get_context_repository() -> ContextRepository:
    """获取上下文仓库"""
    return ContextRepository()


def get_plan_repository() -> PlanRepository:
    """获取计划仓库"""
    return PlanRepository()
