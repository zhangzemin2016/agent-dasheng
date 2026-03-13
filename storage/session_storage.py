"""
会话存储模块
基于统一数据库的会话管理
"""

import time
from typing import Dict, List, Optional, Any

from .database import get_session_repository, SessionRepository
from utils.logger import get_logger

logger = get_logger("storage.session")


class SessionStorage:
    """
    会话存储类
    提供会话的增删改查操作，基于 SQLite 统一数据库
    """

    def __init__(self):
        self._repo = get_session_repository()

    def save_session(self, session: Dict[str, Any]) -> bool:
        """保存会话"""
        # 确保必要字段
        if 'id' not in session:
            logger.error("会话缺少 id 字段")
            return False

        if 'created_at' not in session:
            session['created_at'] = time.time()
        session['updated_at'] = time.time()

        return self._repo.save(session)

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载单个会话"""
        return self._repo.load(session_id)

    def load_all_sessions(self, project_path: str = None) -> List[Dict[str, Any]]:
        """
        加载所有会话

        Args:
            project_path: 可选，按项目路径筛选
        """
        return self._repo.load_all(project_path)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        return self._repo.delete(session_id)

    def save_session_summary(self, session_id: str, summary: str) -> bool:
        """保存会话摘要"""
        return self._repo.update_summary(session_id, summary)

    def load_session_summary(self, session_id: str) -> Optional[str]:
        """加载会话摘要"""
        session = self._repo.load(session_id)
        return session.get('summary') if session else None

    def delete_session_summary(self, session_id: str) -> bool:
        """删除会话摘要（清空摘要字段）"""
        return self._repo.update_summary(session_id, '')

    def clear_all(self) -> bool:
        """清空所有会话"""
        try:
            sessions = self._repo.load_all()
            for session in sessions:
                self._repo.delete(session['id'])
            logger.info("已清空所有会话")
            return True
        except Exception as e:
            logger.error(f"清空会话失败: {e}")
            return False

    def export_session(self, session_id: str, output_path: str) -> bool:
        """导出会话到 JSON 文件"""
        import json
        session = self.load_session(session_id)
        if not session:
            return False

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
            logger.info(f"会话已导出: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出会话失败: {e}")
            return False

    def import_session(self, input_path: str) -> Optional[str]:
        """从 JSON 文件导入会话"""
        import json
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                session = json.load(f)

            if self.save_session(session):
                logger.info(f"会话已导入: {session['id'][:8]}")
                return session['id']
            return None
        except Exception as e:
            logger.error(f"导入会话失败: {e}")
            return None


# 全局存储实例
_storage_instance: Optional[SessionStorage] = None


def get_session_storage() -> SessionStorage:
    """获取全局会话存储实例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = SessionStorage()
    return _storage_instance
