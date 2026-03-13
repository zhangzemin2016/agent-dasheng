"""
Skill 执行器模块
负责执行 skill 的具体逻辑
"""

import os
import re
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass
import asyncio

from .skill_registry import Skill, SkillRegistry, get_skill_registry


@dataclass
class SkillExecutionResult:
    """Skill 执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    artifacts: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts or {}
        }


class SkillExecutor:
    """
    Skill 执行器
    支持多种执行方式：直接执行、脚本执行、Python 函数执行
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or get_skill_registry()
        self.execution_handlers: Dict[str, callable] = {
            'shell': self._execute_shell,
            'python': self._execute_python,
            'script': self._execute_script,
        }
    
    async def execute(
        self, 
        skill_name: str, 
        params: Dict[str, Any] = None,
        working_dir: Optional[str] = None
    ) -> SkillExecutionResult:
        """
        执行指定 skill
        
        Args:
            skill_name: skill 名称或 ID
            params: 执行参数
            working_dir: 工作目录
        
        Returns:
            SkillExecutionResult: 执行结果
        """
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return SkillExecutionResult(
                success=False,
                output="",
                error=f"Skill '{skill_name}' 未找到"
            )
        
        params = params or {}
        working_dir = working_dir or os.getcwd()
        
        try:
            # 检查是否有对应的执行脚本
            if skill.scripts:
                # 优先执行 main.py 或 run.py
                for script_name in ['main.py', 'run.py', 'execute.py']:
                    if script_name in skill.scripts:
                        return await self._execute_script(
                            skill, script_name, params, working_dir
                        )
                # 执行第一个找到的脚本
                first_script = list(skill.scripts.keys())[0]
                return await self._execute_script(
                    skill, first_script, params, working_dir
                )
            
            # 如果没有脚本，解析 instructions 执行
            return await self._execute_from_instructions(skill, params, working_dir)
            
        except Exception as e:
            return SkillExecutionResult(
                success=False,
                output="",
                error=f"执行 skill 时出错: {str(e)}"
            )
    
    async def _execute_script(
        self, 
        skill: Skill, 
        script_name: str,
        params: Dict[str, Any],
        working_dir: str
    ) -> SkillExecutionResult:
        """执行 skill 脚本"""
        script_path = skill.scripts.get(script_name)
        if not script_path:
            return SkillExecutionResult(
                success=False,
                output="",
                error=f"脚本 '{script_name}' 不存在"
            )
        
        # 构建命令
        if script_name.endswith('.py'):
            cmd = ['python', str(script_path)]
        elif script_name.endswith('.sh'):
            cmd = ['bash', str(script_path)]
        else:
            cmd = [str(script_path)]
        
        # 添加参数
        for key, value in params.items():
            cmd.extend([f'--{key}', str(value)])
        
        # 执行命令
        return await self._run_command(cmd, working_dir, skill)
    
    async def _execute_from_instructions(
        self,
        skill: Skill,
        params: Dict[str, Any],
        working_dir: str
    ) -> SkillExecutionResult:
        """从 instructions 解析并执行"""
        instructions = skill.instructions
        
        # 检查是否有明确的执行命令
        # 查找 "## How to run" 或 "## 执行方式" 部分
        run_section_match = re.search(
            r'##\s*(?:How to run|执行方式|运行方式)\s*\n(.*?)(?=\n##|\Z)',
            instructions,
            re.DOTALL | re.IGNORECASE
        )
        
        if run_section_match:
            run_section = run_section_match.group(1).strip()
            # 提取代码块
            code_block_match = re.search(
                r'```(?:\w+)?\n(.*?)\n```',
                run_section,
                re.DOTALL
            )
            if code_block_match:
                command = code_block_match.group(1).strip()
                # 替换参数占位符
                for key, value in params.items():
                    command = command.replace(f'<{key}>', str(value))
                    command = command.replace(f'{{{key}}}', str(value))
                
                # 执行命令
                return await self._run_command(
                    command.split(), 
                    working_dir, 
                    skill
                )
        
        # 如果没有明确的执行命令，返回 instructions 作为指导
        return SkillExecutionResult(
            success=True,
            output=f"Skill '{skill.metadata.name}' 已加载，但没有自动执行脚本。\n\n使用说明:\n{instructions}",
            artifacts={"instructions": instructions}
        )
    
    async def _execute_shell(
        self,
        command: str,
        working_dir: str,
        skill: Skill
    ) -> SkillExecutionResult:
        """执行 shell 命令"""
        return await self._run_command(command.split(), working_dir, skill)
    
    async def _execute_python(
        self,
        code: str,
        working_dir: str,
        skill: Skill
    ) -> SkillExecutionResult:
        """执行 Python 代码"""
        # 创建临时文件执行 Python 代码
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            result = await self._run_command(['python', temp_file], working_dir, skill)
        finally:
            os.unlink(temp_file)
        
        return result
    
    async def _run_command(
        self,
        cmd: List[str],
        working_dir: str,
        skill: Skill
    ) -> SkillExecutionResult:
        """运行命令"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                return SkillExecutionResult(
                    success=True,
                    output=stdout_str,
                    artifacts={"stderr": stderr_str} if stderr_str else None
                )
            else:
                return SkillExecutionResult(
                    success=False,
                    output=stdout_str,
                    error=stderr_str or f"命令执行失败，返回码: {process.returncode}"
                )
                
        except Exception as e:
            return SkillExecutionResult(
                success=False,
                output="",
                error=f"执行命令时出错: {str(e)}"
            )
    
    async def stream_execute(
        self,
        skill_name: str,
        params: Dict[str, Any] = None,
        working_dir: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        流式执行 skill，实时输出结果
        """
        skill = self.registry.get_skill(skill_name)
        if not skill:
            yield json.dumps({
                "type": "error",
                "data": f"Skill '{skill_name}' 未找到"
            }, ensure_ascii=False)
            return
        
        params = params or {}
        working_dir = working_dir or os.getcwd()
        
        yield json.dumps({
            "type": "start",
            "data": f"开始执行 skill: {skill.metadata.name}"
        }, ensure_ascii=False)
        
        try:
            # 简化实现：先执行再分段输出
            result = await self.execute(skill_name, params, working_dir)
            
            if result.success:
                # 分段输出
                chunk_size = 100
                output = result.output
                for i in range(0, len(output), chunk_size):
                    chunk = output[i:i + chunk_size]
                    yield json.dumps({
                        "type": "content",
                        "data": chunk
                    }, ensure_ascii=False)
                
                yield json.dumps({
                    "type": "done",
                    "data": result.output
                }, ensure_ascii=False)
            else:
                yield json.dumps({
                    "type": "error",
                    "data": result.error or "执行失败"
                }, ensure_ascii=False)
                
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "data": f"执行出错: {str(e)}"
            }, ensure_ascii=False)


# 便捷函数
async def execute_skill(
    skill_name: str,
    params: Dict[str, Any] = None,
    working_dir: Optional[str] = None
) -> SkillExecutionResult:
    """便捷函数：执行 skill"""
    executor = SkillExecutor()
    return await executor.execute(skill_name, params, working_dir)


def get_skill_info(skill_name: str) -> Optional[Dict[str, Any]]:
    """获取 skill 信息"""
    registry = get_skill_registry()
    skill = registry.get_skill(skill_name)
    if not skill:
        return None
    
    return {
        "id": skill.id,
        "name": skill.metadata.name,
        "description": skill.metadata.description,
        "version": skill.metadata.version,
        "author": skill.metadata.author,
        "tags": skill.metadata.tags,
        "scripts": list(skill.scripts.keys()),
        "assets": list(skill.assets.keys())
    }


def list_all_skills() -> List[Dict[str, Any]]:
    """列出所有 skills"""
    registry = get_skill_registry()
    skills = registry.list_skills()
    return [
        {
            "id": s.id,
            "name": s.metadata.name,
            "description": s.metadata.description,
            "version": s.metadata.version,
            "tags": s.metadata.tags
        }
        for s in skills
    ]
