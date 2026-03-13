"""
网络访问工具模块
提供网页内容获取、搜索引擎、API 请求等网络功能
适配 DeepAgents 框架
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import quote
from langchain_core.tools import tool


@tool("获取网页内容")
def fetch_webpage(url: str, extract_text: bool = True) -> str:
    """
    获取网页内容并提取精要摘要

    Args:
        url: 网页 URL
        extract_text: 是否只提取文本内容（去除 HTML 标签），默认为 True

    Returns:
        网页摘要信息和链接
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        if extract_text:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 移除脚本、样式和其他非主要内容
            for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                script.decompose()

            # 提取标题
            title = soup.title.string if soup.title else '无标题'

            # 尝试提取主要内容
            main_content = None

            # 优先查找 article、main 标签
            for tag in ['article', 'main']:
                main_tag = soup.find(tag)
                if main_tag:
                    main_content = main_tag
                    break

            # 如果没有，查找 class 包含 content、post、article 的元素
            if not main_content:
                for class_name in ['content', 'post', 'article', 'entry', 'main-content']:
                    main_tag = soup.find(class_=class_name)
                    if main_tag:
                        main_content = main_tag
                        break

            # 如果还是没有，使用整个 body
            if not main_content:
                main_content = soup.find('body') or soup

            # 提取段落
            paragraphs = main_content.find_all('p')

            # 提取前 3 个有意义的段落作为摘要
            summary_paragraphs = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    summary_paragraphs.append(text)
                    if len(summary_paragraphs) >= 3:
                        break

            # 构建摘要
            if summary_paragraphs:
                summary = '\n\n'.join(summary_paragraphs)
                if len(summary) > 800:
                    summary = summary[:800] + '...'
            else:
                text = main_content.get_text(separator=' ', strip=True)
                summary = text[:500] + '...' if len(text) > 500 else text

            result = f"📄 **{title}**\n\n🔗 **链接**: {url}\n\n📝 **内容摘要**:\n{summary}\n\n💡 *点击上方链接访问完整内容*"
            return result
        else:
            return response.text[:5000]

    except requests.exceptions.Timeout:
        return "❌ 请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return "❌ 网络连接错误，请检查网络或 URL 是否正确"
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP 错误：{e.response.status_code}"
    except Exception as e:
        return f"❌ 获取网页失败：{str(e)}"


@tool("网络搜索")
def web_search(query: str, num_results: int = 5) -> str:
    """
    执行网络搜索（使用百度）

    Args:
        query: 搜索关键词
        num_results: 返回结果数量，默认为 5

    Returns:
        搜索结果列表
    """
    try:
        # 使用百度搜索
        search_url = f"https://www.baidu.com/s?wd={quote(query)}&rn={num_results}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # 提取百度搜索结果
        result_elements = soup.find_all('div', class_='result')

        for result in result_elements[:num_results]:
            title_elem = result.find('h3', class_='t')
            link_elem = result.find('a')
            content_elem = result.find(
                'div', class_='c-abstract') or result.find('div', class_='general-wrapper')

            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                snippet = content_elem.get_text(
                    strip=True)[:200] if content_elem else ''

                result_text = f"📌 {title}"
                if url:
                    result_text += f"\n   🔗 {url}"
                if snippet:
                    result_text += f"\n   {snippet}..."

                results.append(result_text)

        if not results:
            return "未找到相关结果，请尝试其他关键词"

        return f"🔍 搜索结果（共 {len(results)} 条）:\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"❌ 搜索失败：{str(e)}\n\n提示：如果网络连接受限，可能需要配置代理或检查网络设置"


@tool("HTTP请求")
def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 10
) -> str:
    """
    发送 HTTP 请求

    Args:
        url: 请求 URL
        method: HTTP 方法（GET/POST/PUT/DELETE），默认为 GET
        headers: 请求头字典（可选）
        json_data: JSON 格式的请求体（可选）
        timeout: 超时时间（秒），默认为 10

    Returns:
        响应内容（JSON 或文本）
    """
    try:
        methods = {
            'GET': requests.get,
            'POST': requests.post,
            'PUT': requests.put,
            'DELETE': requests.delete,
            'PATCH': requests.patch
        }

        if method.upper() not in methods:
            return f"❌ 不支持的 HTTP 方法：{method}"

        request_func = methods[method.upper()]

        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }

        if headers:
            default_headers.update(headers)

        response = request_func(
            url,
            headers=default_headers,
            json=json_data,
            timeout=timeout
        )
        response.raise_for_status()

        # 尝试解析为 JSON
        try:
            import json
            import pprint
            json_resp = response.json()
            formatted = pprint.pformat(json_resp, indent=2, width=80)
            return f"✅ 响应状态码：{response.status_code}\n\n响应内容:\n{formatted[:3000]}"
        except:
            return f"✅ 响应状态码：{response.status_code}\n\n响应内容:\n{response.text[:3000]}"

    except requests.exceptions.Timeout:
        return "❌ 请求超时"
    except requests.exceptions.ConnectionError:
        return "❌ 连接错误，请检查 URL 或网络"
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP 错误：{e.response.status_code} - {e.response.reason}"
    except Exception as e:
        return f"❌ 请求失败：{str(e)}"


@tool("查询维基百科")
def query_wikipedia(search_term: str) -> str:
    """
    查询维基百科条目（支持多语言版本）

    Args:
        search_term: 搜索词条

    Returns:
        维基百科条目摘要
    """
    try:
        # 尝试多个 Wikipedia 镜像/API 端点
        wikipedia_endpoints = [
            {
                'name': '中文维基百科',
                'api_url': 'https://zh.wikipedia.org/w/api.php',
                'lang': 'zh'
            },
            {
                'name': '英文维基百科',
                'api_url': 'https://en.wikipedia.org/w/api.php',
                'lang': 'en'
            },
        ]

        last_error = None

        for endpoint in wikipedia_endpoints:
            try:
                api_url = endpoint['api_url']

                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'search',
                    'srsearch': search_term,
                    'srlimit': 1
                }

                response = requests.get(api_url, params=params, timeout=8)
                response.raise_for_status()
                data = response.json()

                search_results = data.get('query', {}).get('search', [])

                if not search_results:
                    continue

                title = search_results[0]['title']
                snippet = search_results[0].get('snippet', '').replace(
                    '<span class="searchmatch">', '').replace('</span>', '')

                # 获取完整页面摘要
                page_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': title,
                    'prop': 'extracts',
                    'exintro': True,
                    'explaintext': True
                }

                page_response = requests.get(
                    api_url, params=page_params, timeout=8)
                page_response.raise_for_status()
                page_data = page_response.json()

                pages = page_data.get('query', {}).get('pages', {})
                extract = ""
                for page in pages.values():
                    extract = page.get('extract', '')
                    break

                if extract:
                    return f"📖 {title} ({endpoint['name']})\n\n🔍 简介:\n{snippet}\n\n{'='*50}\n\n📝 摘要:\n{extract[:1500]}\n\n💡 *内容来自{endpoint['name']}*"

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                last_error = f"{endpoint['name']}无法访问"
                continue
            except Exception as e:
                last_error = str(e)
                continue

        if last_error:
            return f"❌ 无法访问维基百科服务\n\n可能原因:\n- 网络连接问题\n- 维基百科服务暂时不可用\n\n💡 建议:\n1. 检查网络连接\n2. 尝试使用百度搜索获取相关信息\n3. 稍后重试"

        return f"未在维基百科中找到关于 '{search_term}' 的条目"

    except Exception as e:
        return f"❌ 查询失败：{str(e)}\n\n💡 建议：可以尝试使用百度搜索获取相关信息"


@tool("获取RSS订阅")
def fetch_rss(feed_url: str, max_entries: int = 10) -> str:
    """
    获取并解析 RSS/Atom 订阅源

    Args:
        feed_url: RSS 订阅 URL
        max_entries: 最大返回条目数，默认为 10

    Returns:
        RSS 条目列表
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'xml')

        # 尝试解析 RSS 2.0
        items = soup.find_all('item')

        # 如果不是 RSS，尝试 Atom
        if not items:
            items = soup.find_all('entry')

        if not items:
            return "❌ 未找到任何 RSS/Atom 条目"

        entries = []
        for item in items[:max_entries]:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate') or item.find('published')
            description = item.find('description') or item.find('summary')

            entry_text = f"📌 {title.get_text(strip=True) if title else '无标题'}"
            if link:
                link_text = link.get_text(strip=True) if isinstance(
                    link.get_text(), str) else link.get('href', '')
                entry_text += f"\n   🔗 {link_text}"
            if pub_date:
                entry_text += f"\n   📅 {pub_date.get_text(strip=True)}"
            if description:
                desc_text = description.get_text(strip=True)[:200]
                entry_text += f"\n   {desc_text}..."

            entries.append(entry_text)

        return f"📰 RSS 订阅（最新 {len(entries)} 条）:\n\n" + "\n\n".join(entries)

    except Exception as e:
        return f"❌ 获取 RSS 失败：{str(e)}"
