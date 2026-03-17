"""
代码分析工具
提供语法检查、依赖分析、代码统计等功能
适配 DeepAgents 框架
"""

import os
import re
import json
import subprocess
import fnmatch
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool
from .common import resolve_path



@tool
def check_syntax(file_path: str, language: Optional[str] = None, workdir: Optional[str] = None) -> str:
    """
    检查代码文件的语法正确性

    Args:
        file_path: 代码文件路径
        language: 语言类型（可选，自动从文件扩展名推断）
                  支持: python, javascript, typescript, go, rust, java

    Returns:
        语法检查结果
    """
    try:
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"

        # 自动推断语言
        if not language:
            ext = os.path.splitext(file_path)[1].lower()
            lang_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.go': 'go',
                '.rs': 'rust',
                '.java': 'java',
            }
            language = lang_map.get(ext)
            if not language:
                return f"❌ 无法识别文件类型: {ext}，请手动指定 language 参数"

        language = language.lower()

        # 根据语言选择检查方式
        if language == 'python':
            return _check_python_syntax(file_path_str)
        elif language in ['javascript', 'typescript']:
            return _check_js_ts_syntax(file_path_str, language)
        elif language == 'go':
            return _check_go_syntax(file_path_str)
        elif language == 'rust':
            return _check_rust_syntax(file_path_str)
        elif language == 'java':
            return _check_java_syntax(file_path_str)
        else:
            return f"⚠️ 暂不支持 {language} 的语法检查"

    except Exception as e:
        return f"❌ 语法检查时出错: {str(e)}"


def _check_python_syntax(file_path: str) -> str:
    """检查 Python 语法"""
    try:
        result = subprocess.run(
            ['python', '-m', 'py_compile', file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"✅ Python 语法检查通过: {file_path}"
        else:
            return f"❌ Python 语法错误:\n{result.stderr}"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


def _check_js_ts_syntax(file_path: str, language: str) -> str:
    """检查 JavaScript/TypeScript 语法"""
    try:
        result = subprocess.run(
            ['npx', 'tsc', '--noEmit', '--skipLibCheck', '--allowJs', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return f"✅ {language.title()} 语法检查通过: {file_path}"
        else:
            errors = result.stdout or result.stderr
            return f"❌ {language.title()} 语法错误:\n{errors[:500]}"
    except subprocess.TimeoutExpired:
        return f"⚠️ 语法检查超时，请确保已安装 TypeScript"
    except FileNotFoundError:
        return f"⚠️ 未找到 tsc，请安装 TypeScript: npm install -g typescript"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


def _check_go_syntax(file_path: str) -> str:
    """检查 Go 语法"""
    try:
        result = subprocess.run(
            ['go', 'vet', file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"✅ Go 语法检查通过: {file_path}"
        else:
            return f"❌ Go 语法/规范问题:\n{result.stderr}"
    except FileNotFoundError:
        return "⚠️ 未找到 go 命令，请安装 Go"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


def _check_rust_syntax(file_path: str) -> str:
    """检查 Rust 语法"""
    try:
        result = subprocess.run(
            ['rustc', '--crate-type', 'lib', '-Z', 'parse-only', file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"✅ Rust 语法检查通过: {file_path}"
        else:
            return f"❌ Rust 语法错误:\n{result.stderr[:500]}"
    except FileNotFoundError:
        return "⚠️ 未找到 rustc，请安装 Rust"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


def _check_java_syntax(file_path: str) -> str:
    """检查 Java 语法"""
    try:
        result = subprocess.run(
            ['javac', '-d', '/tmp/compiled', '-sourcepath',
             os.path.dirname(file_path), file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"✅ Java 语法检查通过: {file_path}"
        else:
            return f"❌ Java 语法错误:\n{result.stderr[:500]}"
    except FileNotFoundError:
        return "⚠️ 未找到 javac，请安装 JDK"
    except Exception as e:
        return f"❌ 检查失败: {str(e)}"


@tool
def analyze_dependencies(project_path: str, language: Optional[str] = None, workdir: Optional[str] = None) -> str:
    """
    分析项目的依赖关系

    Args:
        project_path: 项目根目录路径
        language: 语言类型（可选，自动检测）

    Returns:
        依赖分析报告
    """
    try:
        if not os.path.isdir(project_path):
            return f"❌ 目录不存在: {project_path}"

        # 自动检测语言
        if not language:
            if os.path.exists(os.path.join(project_path_str, 'requirements.txt')):
                language = 'python'
            elif os.path.exists(os.path.join(project_path_str, 'package.json')):
                language = 'javascript'
            elif os.path.exists(os.path.join(project_path_str, 'go.mod')):
                language = 'go'
            elif os.path.exists(os.path.join(project_path_str, 'Cargo.toml')):
                language = 'rust'
            elif os.path.exists(os.path.join(project_path_str, 'pom.xml')) or \
                    os.path.exists(os.path.join(project_path_str, 'build.gradle')):
                language = 'java'

        if not language:
            return "❌ 无法自动检测项目类型，请手动指定 language 参数"

        language = language.lower()

        if language == 'python':
            return _analyze_python_deps(project_path_str)
        elif language == 'javascript':
            return _analyze_js_deps(project_path_str)
        elif language == 'go':
            return _analyze_go_deps(project_path_str)
        elif language == 'rust':
            return _analyze_rust_deps(project_path_str)
        else:
            return f"⚠️ 暂不支持 {language} 的依赖分析"

    except Exception as e:
        return f"❌ 依赖分析时出错: {str(e)}"


def _analyze_python_deps(project_path: str) -> str:
    """分析 Python 依赖"""
    results = []

    # 检查 requirements.txt
    req_file = os.path.join(project_path, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            deps = [line.strip() for line in f if line.strip()
                    and not line.startswith('#')]
        results.append(f"📦 requirements.txt 依赖 ({len(deps)} 个):")
        for dep in deps[:20]:
            results.append(f"  - {dep}")
        if len(deps) > 20:
            results.append(f"  ... 等共 {len(deps)} 个")

    # 检查 pyproject.toml
    pyproject_file = os.path.join(project_path, 'pyproject.toml')
    if os.path.exists(pyproject_file):
        results.append(f"\n📦 发现 pyproject.toml（现代 Python 项目配置）")

    # 检查导入语句
    try:
        imports = set()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(
                '.') and d not in ['venv', '__pycache__', 'bak']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        for match in re.finditer(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE):
                            imports.add(match.group(1))
                    except:
                        continue

        stdlib_modules = {'os', 'sys', 'json', 're', 'subprocess', 'typing', 'pathlib', 'datetime',
                          'collections', 'itertools', 'functools', 'math', 'random', 'string',
                          'hashlib', 'base64', 'urllib', 'http', 'socket', 'threading',
                          'multiprocessing', 'asyncio', 'unittest', 'pytest', 'fnmatch'}
        third_party = imports - stdlib_modules

        if third_party:
            results.append(f"\n📊 代码中使用的第三方库 ({len(third_party)} 个):")
            for imp in sorted(third_party)[:20]:
                results.append(f"  - {imp}")
    except:
        pass

    return '\n'.join(results) if results else "⚠️ 未找到依赖信息"


def _analyze_js_deps(project_path: str) -> str:
    """分析 JavaScript/Node.js 依赖"""
    results = []

    package_file = os.path.join(project_path, 'package.json')
    if os.path.exists(package_file):
        with open(package_file, 'r', encoding='utf-8') as f:
            package = json.load(f)

        deps = package.get('dependencies', {})
        dev_deps = package.get('devDependencies', {})

        if deps:
            results.append(f"📦 生产依赖 ({len(deps)} 个):")
            for name, version in list(deps.items())[:15]:
                results.append(f"  - {name}@{version}")

        if dev_deps:
            results.append(f"\n📦 开发依赖 ({len(dev_deps)} 个):")
            for name, version in list(dev_deps.items())[:10]:
                results.append(f"  - {name}@{version}")

    return '\n'.join(results) if results else "⚠️ 未找到 package.json"


def _analyze_go_deps(project_path: str) -> str:
    """分析 Go 依赖"""
    go_mod_file = os.path.join(project_path, 'go.mod')
    if os.path.exists(go_mod_file):
        with open(go_mod_file, 'r', encoding='utf-8') as f:
            content = f.read()

        requires = re.findall(r'require\s+([^\s]+)\s+([^\s\n]+)', content)

        results = [f"📦 Go 模块依赖 ({len(requires)} 个):"]
        for mod, version in requires[:20]:
            results.append(f"  - {mod} {version}")

        return '\n'.join(results)

    return "⚠️ 未找到 go.mod"


def _analyze_rust_deps(project_path: str) -> str:
    """分析 Rust 依赖"""
    cargo_file = os.path.join(project_path, 'Cargo.toml')
    if os.path.exists(cargo_file):
        with open(cargo_file, 'r', encoding='utf-8') as f:
            content = f.read()

        deps_match = re.search(
            r'\[dependencies\](.*?)(?=\[|$)', content, re.DOTALL)
        if deps_match:
            deps_section = deps_match.group(1)
            deps = re.findall(
                r'^(\w+)\s*=\s*"([^"]+)"', deps_section, re.MULTILINE)

            results = [f"📦 Rust 依赖 ({len(deps)} 个):"]
            for name, version in deps[:20]:
                results.append(f"  - {name} = \"{version}\"")

            return '\n'.join(results)

    return "⚠️ 未找到 Cargo.toml 或依赖信息"


@tool
def code_statistics(path: str, file_pattern: str = "*", workdir: Optional[str] = None) -> str:
    """
    统计代码文件信息（行数、文件数等）

    Args:
        path: 目录或文件路径
        file_pattern: 文件匹配模式，如 "*.py"、"*.js"

    Returns:
        统计结果
    """
    try:
        if not os.path.exists(path):
            return f"❌ 路径不存在: {path}"

        stats = {
            'files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0
        }

        def analyze_file(file_path: str):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                total = len(lines)
                blank = sum(1 for line in lines if line.strip() == '')

                ext = os.path.splitext(file_path)[1].lower()
                comment_prefixes = {
                    '.py': ['#'],
                    '.js': ['//', '/*', '*'],
                    '.ts': ['//', '/*', '*'],
                    '.java': ['//', '/*', '*'],
                    '.go': ['//', '/*'],
                    '.rs': ['//', '/*', '*', '//!', '///'],
                }

                prefixes = comment_prefixes.get(ext, ['#', '//'])
                comments = sum(1 for line in lines if any(
                    line.strip().startswith(p) for p in prefixes))

                return {
                    'total': total,
                    'blank': blank,
                    'comment': comments,
                    'code': total - blank - comments
                }
            except:
                return None

        if os.path.isfile(path_str):
            result = analyze_file(path)
            if result:
                stats['files'] = 1
                stats['total_lines'] = result['total']
                stats['code_lines'] = result['code']
                stats['comment_lines'] = result['comment']
                stats['blank_lines'] = result['blank']
        else:
            for root, dirs, files in os.walk(path_str):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    'node_modules', '__pycache__', 'venv', '.git', 'target', 'dist', 'build', 'bak']]

                for filename in files:
                    if fnmatch.fnmatch(filename, file_pattern):
                        file_path = os.path.join(root, filename)
                        result = analyze_file(file_path)
                        if result:
                            stats['files'] += 1
                            stats['total_lines'] += result['total']
                            stats['code_lines'] += result['code']
                            stats['comment_lines'] += result['comment']
                            stats['blank_lines'] += result['blank']

        if stats['code_lines'] > 0:
            return f"""📊 代码统计结果

文件数: {stats['files']}
总行数: {stats['total_lines']:,}
代码行: {stats['code_lines']:,}
注释行: {stats['comment_lines']:,}
空行: {stats['blank_lines']:,}

代码注释比: {stats['comment_lines'] / stats['code_lines'] * 100:.1f}% (注释行/代码行)"""
        else:
            return f"""📊 代码统计结果

文件数: {stats['files']}
总行数: {stats['total_lines']:,}"""

    except Exception as e:
        return f"❌ 统计时出错: {str(e)}"


def get_code_tools():
    """获取所有代码分析工具"""
    return [
        check_syntax,
        analyze_dependencies,
        code_statistics,
    ]

# 工具名称映射（用于显示中文名称）
TOOL_DISPLAY_NAMES = {
    "check_syntax": "语法检查",
    "analyze_dependencies": "依赖分析",
    "code_statistics": "代码统计",
}


def get_code_tools():
    """获取所有代码分析工具"""
    return [
        check_syntax,
        analyze_dependencies,
        code_statistics,
    ]
