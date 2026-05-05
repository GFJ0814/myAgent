# MyAgent

一个轻量级的 Agent 框架，支持工具调用（Tools）与复合技能（Skills），提供 **CLI** 与 **Web 前端对话页面** 双入口。

## Features
- 基于 OpenAI 兼容协议（豆包 / 火山方舟 Ark）的推理循环
- 原子工具：`shell_exec` / `file_read` / `file_write` / `python_exec` / `news_search`
- 基于目录扫描的 Skills 加载（`skills/**/SKILL.md` + YAML frontmatter）
- CLI 与 Web 双入口共用统一 `AgentService`，逻辑不分叉
- **内置 Web 对话前端**，三栏布局参考主流 Agent 设计（会话列表 / 对话流 / 技能面板）
- 多会话管理、工具调用折叠展示、`localStorage` 持久化

## Architecture
```
┌──────────┐     ┌──────────┐
│   cli.py │     │ server.py│    <- 入口适配层（CLI / FastAPI）
└────┬─────┘     └────┬─────┘
     └─────┬──────────┘
           ▼
     ┌──────────────┐
     │ AgentService │             <- 服务层（统一封装）
     └──────┬───────┘
       ┌────┴─────┐
       ▼          ▼
┌─────────────┐ ┌──────────────┐
│ agent_core  │ │ session_store│   <- 推理循环 / 多会话存储
│ tools.py    │ │              │
│ skill_loader│ │              │
└─────────────┘ └──────────────┘
```

## Installation
1. 克隆仓库
   ```bash
   git clone https://github.com/GFJ0814/myAgent.git
   cd myAgent
   ```
2. 创建虚拟环境并安装依赖
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. 配置环境变量
   ```bash
   export ARK_API_KEY=你的火山方舟 API Key
   ```

## Usage

### CLI 模式
```bash
python cli.py
```
- 输入 `clear` 清空当前会话
- 输入 `exit` 退出

### Web 模式（含对话前端）
```bash
uvicorn server:app --host 127.0.0.1 --port 8000
```
启动后在浏览器打开 **<http://127.0.0.1:8000/>** 即可使用内置对话页面。

页面功能：
- **左侧**：会话列表，支持新建 / 切换 / 清空，`localStorage` 持久化
- **中间**：消息流 + 输入框，Enter 发送，Shift+Enter 换行
- **右侧**：可用 Skills 面板
- Assistant 触发工具或技能调用时，以可折叠块展示 **工具名 / 参数 / 结果**

### API 接口
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 返回前端页面 |
| GET | `/health` | 健康检查 |
| POST | `/sessions` | 新建会话 |
| GET | `/sessions` | 列出会话 |
| GET | `/sessions/{id}/messages` | 获取会话历史消息 |
| POST | `/sessions/{id}/clear` | 清空指定会话 |
| POST | `/chat` | 发送消息 |
| GET | `/skills` | 列出可用 Skills |

## Skills 编写
在 `skills/<分组>/<skill_name>/SKILL.md` 中定义一个技能，文件头部使用 YAML frontmatter：

```markdown
---
name: tell_joke
description: 讲一个冷笑话
enabled: true
---

# Instructions
向用户讲一个简短的冷笑话。
```

启动时 `skill_loader` 会递归扫描并自动注册。

## Project Layout
```
agent_core.py       # 推理循环、能力加载
agent_service.py    # 服务层，CLI / Web 共用
session_store.py    # 会话存储（内存 + 线程安全）
cli.py              # CLI 入口
server.py           # FastAPI 入口，挂载前端
tools.py            # 原子工具
skill_loader.py     # Skills 目录扫描器
skills/             # SKILL.md 技能定义
frontend/           # 内置对话前端（HTML / CSS / JS）
```

## License
MIT License
