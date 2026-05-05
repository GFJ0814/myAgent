from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
import os
import subprocess
import sys
import tempfile
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


def shell_exec(command: str) -> str:
    """执行 shell 命令并返回 stdout + stderr。"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "[error] command timed out after 30s"
    except Exception as e:
        return f"[error] {e}"


def file_read(path: str) -> str:
    """读取文件内容。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[error] {e}"


def file_write(path: str, content: str) -> str:
    """将内容写入文件（自动创建父目录）。"""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"OK - wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"[error] {e}"


def python_exec(code: str) -> str:
    """在子进程中执行 Python 代码并返回输出。"""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "[error] execution timed out after 30s"
    except Exception as e:
        return f"[error] {e}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def news_search(query: str, limit: int = 5) -> str:
    """检索最近一天的实时新闻标题与链接。"""
    normalized_query = query.strip()
    if not normalized_query:
        return "[error] query must not be empty"

    if limit <= 0:
        return "[error] limit must be greater than 0"

    sources = [
        (
            "Google News",
            "https://news.google.com/rss/search?q="
            + quote_plus(f"{normalized_query} when:1d")
            + "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        ),
        (
            "Bing News",
            "https://www.bing.com/news/search?q="
            + quote_plus(normalized_query)
            + "&format=rss",
        ),
    ]

    errors: list[str] = []
    for source_name, url in sources:
        try:
            items = _fetch_rss_items(url, limit)
        except Exception as e:
            errors.append(f"{source_name}: {e}")
            continue

        if items:
            today = datetime.now().astimezone().date().isoformat()
            lines = [f"Latest news for '{normalized_query}' on {today} from {source_name}:"]
            for index, item in enumerate(items, start=1):
                lines.append(f"{index}. {item['title']}")
                if item["published_at"]:
                    lines.append(f"   published: {item['published_at']}")
                lines.append(f"   link: {item['link']}")
            return "\n".join(lines)

    if errors:
        return "[error] failed to fetch news: " + " | ".join(errors)
    return f"[error] no recent news found for query: {normalized_query}"


def _fetch_rss_items(url: str, limit: int) -> list[dict[str, str]]:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=15) as response:
        payload = response.read()

    root = ET.fromstring(payload)
    items: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        title = _xml_text(item.find("title"))
        link = _xml_text(item.find("link"))
        pub_date_raw = _xml_text(item.find("pubDate"))
        published_at = _format_pub_date(pub_date_raw)
        if not title or not link:
            continue
        items.append(
            {
                "title": unescape(title),
                "link": link,
                "published_at": published_at,
            }
        )
        if len(items) >= limit:
            break

    return items


def _xml_text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _format_pub_date(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone().isoformat(timespec="seconds")
    except Exception:
        return value


TOOLS = {
    "shell_exec": {
        "function": shell_exec,
        "schema": {
            "type": "function",
            "function": {
                "name": "shell_exec",
                "description": "Execute a shell command and return its output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute.",
                        }
                    },
                    "required": ["command"],
                },
            },
        },
    },
    "file_read": {
        "function": file_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "file_read",
                "description": "Read the contents of a file at the given path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative file path.",
                        }
                    },
                    "required": ["path"],
                },
            },
        },
    },
    "file_write": {
        "function": file_write,
        "schema": {
            "type": "function",
            "function": {
                "name": "file_write",
                "description": "Write content to a file (creates parent directories if needed).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative file path.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write.",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
    },
    "python_exec": {
        "function": python_exec,
        "schema": {
            "type": "function",
            "function": {
                "name": "python_exec",
                "description": "Execute Python code in a subprocess and return its output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python source code to execute.",
                        }
                    },
                    "required": ["code"],
                },
            },
        },
    },
    "news_search": {
        "function": news_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "news_search",
                "description": "Search recent real-time news from public RSS sources and return current headlines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The topic or event to search in recent news.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of headlines to return.",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    },
}
