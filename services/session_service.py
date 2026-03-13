"""
会话管理服务
负责会话的创建、加载、切换、保存等操作
"""

import time
import uuid
from typing import Dict, List, Optional
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("services.session")


class SessionService:
    """会话管理服务"""

    def __init__(self):
        self.sessions: List[Dict] = []
        self.current_session_id: Optional[str] = None

    def create_session(self, title: str = "新对话") -> Dict:
        """创建新会话"""
        session = {
            "id": str(uuid.uuid4()),
            "title": title,
            "messages": [],
            "created_at": time.time(),
            "updated_at": time.time(),
            "summary": None  # 对话摘要
        }
        self.sessions.insert(0, session)
        self.current_session_id = session["id"]
        logger.info(f"创建新会话：{session['id'][:8]}")
        return session

    def get_current_session(self) -> Optional[Dict]:
        """获取当前会话"""
        if not self.current_session_id:
            return None

        for session in self.sessions:
            if session["id"] == self.current_session_id:
                return session
        return None

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取指定会话"""
        for session in self.sessions:
            if session["id"] == session_id:
                return session
        return None

    def set_current_session(self, session_id: str) -> bool:
        """设置当前会话"""
        if session_id == self.current_session_id:
            return True

        # 验证会话是否存在
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"会话不存在：{session_id}")
            return False

        self.current_session_id = session_id
        logger.info(f"切换到会话：{session_id[:8]}")
        return True

    def add_message(self, role: str, content: str) -> None:
        """添加消息到当前会话"""
        session = self.get_current_session()
        if not session:
            logger.error("没有当前会话")
            return

        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        session["messages"].append(message)
        session["updated_at"] = time.time()

        # 如果是第一条用户消息，更新标题
        user_messages = [m for m in session["messages"] if m["role"] == "user"]
        if len(user_messages) == 1 and role == "user":
            session["title"] = content[:20] + \
                ("..." if len(content) > 20 else "")

    def update_message(self, index: int, content: str, completed: bool = False) -> None:
        """更新指定索引的消息"""
        session = self.get_current_session()
        if not session or index >= len(session["messages"]):
            return

        session["messages"][index]["content"] = content
        session["messages"][index]["completed"] = completed
        session["updated_at"] = time.time()

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if len(self.sessions) <= 1:
            logger.warning("无法删除最后一个会话")
            return False

        # 找到并删除会话
        for i, session in enumerate(self.sessions):
            if session["id"] == session_id:
                self.sessions.pop(i)
                logger.info(f"删除会话：{session_id[:8]}")

                # 如果删除的是当前会话，切换到第一个
                if session_id == self.current_session_id:
                    self.current_session_id = self.sessions[0]["id"]

                return True

        return False

    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话"""
        return self.sessions.copy()

    def clear_all_sessions(self) -> None:
        """清空所有会话（保留一个）"""
        if self.sessions:
            self.sessions = [self.sessions[0]]
            self.current_session_id = self.sessions[0]["id"]
            logger.info("清空所有会话")

    def get_messages(self, session_id: str) -> List[Dict]:
        """获取指定会话的消息列表"""
        session = self.get_session(session_id)
        return session["messages"] if session else []

    def set_session_summary(self, session_id: str, summary: str) -> bool:
        """设置会话摘要"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"会话不存在：{session_id}")
            return False

        session["summary"] = summary
        session["updated_at"] = time.time()
        logger.info(f"已设置会话摘要：{session_id[:8]}")
        return True

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """获取会话摘要"""
        session = self.get_session(session_id)
        if not session:
            return None
        return session.get("summary")

    def generate_summary(self, session_id: str) -> Optional[str]:
        """根据对话内容生成摘要"""
        session = self.get_session(session_id)
        if not session:
            return None

        messages = session.get("messages", [])
        if not messages:
            return "暂无对话内容"

        # 提取关键信息生成摘要
        user_messages = [m for m in messages if m["role"] == "user"]
        ai_messages = [m for m in messages if m["role"] == "assistant"]

        # 简单的摘要策略：统计对话轮次和主题
        summary_lines = [
            f"# 对话摘要",
            f"",
            f"**创建时间**: {self._format_timestamp(session['created_at'])}",
            f"**最后更新**: {self._format_timestamp(session['updated_at'])}",
            f"**对话轮次**: {len(messages)} 条消息",
            f"**用户提问**: {len(user_messages)} 次",
            f"**AI 回复**: {len(ai_messages)} 次",
            f"",
            f"## 对话概要",
            f""
        ]

        # 如果第一条用户消息存在，作为主题
        if user_messages:
            first_topic = user_messages[0]["content"][:100]
            if len(user_messages[0]["content"]) > 100:
                first_topic += "..."
            summary_lines.append(f"**主题**: {first_topic}")
            summary_lines.append("")

        # 列出主要话题（前 5 条用户消息）
        if len(user_messages) > 1:
            summary_lines.append("**主要话题**:")
            for i, msg in enumerate(user_messages[:5], 1):
                topic = msg["content"][:50].replace("\n", " ")
                if len(msg["content"]) > 50:
                    topic += "..."
                summary_lines.append(f"{i}. {topic}")

        return "\n".join(summary_lines)

    def _format_timestamp(self, timestamp: float) -> str:
        """格式化时间戳"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        """转换为字典格式（用于序列化）"""
        return {
            "sessions": self.sessions,
            "current_session_id": self.current_session_id
        }

    def from_dict(self, data: Dict) -> None:
        """从字典加载数据"""
        self.sessions = data.get("sessions", [])
        self.current_session_id = data.get("current_session_id")
        logger.info(f"加载了 {len(self.sessions)} 个会话")
