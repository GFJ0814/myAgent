# 新增对话前端页面 Spec

## Why
当前项目仅提供 CLI 与 FastAPI 后端接口，Web 用户必须借助 curl/Postman 才能对话，体验差、传播成本高。需要一个内置的对话前端，让使用者直接在浏览器里完成 Agent 交互，并参考主流 Agent 产品（ChatGPT / Claude / Cursor）的界面范式，展示消息气泡、工具与 Skill 调用过程。

## What Changes
- 新增 `frontend/` 目录，提供纯静态的对话前端（HTML + CSS + 原生 JS，不引入构建工具与前端框架），降低复杂度。
- 前端通过调用已有的 `server.py` 接口（`/sessions`、`/chat`、`/skills`、`/sessions/{id}/clear`）完成交互。
- 在 `server.py` 中挂载静态文件（`StaticFiles`），以根路径 `/` 提供前端入口，使单端口即可访问 UI 与 API。
- **BREAKING**：`server.py` 根路径 `/` 由原来的"无定义/可能 404"变更为返回前端页面；如有调用方依赖根路径的 JSON 响应，需改用 `/health`。
- 前端界面参考主流 Agent 设计：左侧会话列表面板 + 主区消息流 + 底部输入框 + 右侧（或抽屉式）技能面板。
- 支持基础能力：新建会话、切换会话、清空会话、发送消息、展示 Assistant/User 消息气泡、展示工具/Skill 调用过程（折叠式）、展示可用 Skills 列表。

## Impact
- Affected specs: `chat-service`（新增 Web UI 交互面）、`skills-registry`（前端读取并展示）。
- Affected code:
  - [server.py](file:///Users/bytedance/ai_project/myAgent/server.py)：挂载静态资源，补充跨端跨域（CORS，按需）、可能补充 `GET /sessions/{id}` 读取历史消息接口。
  - [agent_service.py](file:///Users/bytedance/ai_project/myAgent/agent_service.py)：若前端需要回放历史，可能新增 `get_history(session_id)` 方法（基于 `SessionStore.get_messages`）。
  - 新增 `frontend/index.html`、`frontend/app.js`、`frontend/styles.css`。
  - [README.md](file:///Users/bytedance/ai_project/myAgent/README.md)：更新启动说明，说明访问 `http://127.0.0.1:8000/`。

## ADDED Requirements

### Requirement: 提供内置对话前端页面
系统 SHALL 在启动 Web 服务后，通过根路径 `/` 返回一个可直接使用的对话前端页面，无需额外构建步骤。

#### Scenario: 首次访问展示空对话
- **WHEN** 用户在浏览器打开 `http://127.0.0.1:8000/`
- **THEN** 页面加载成功，展示空对话区、底部输入框、左侧会话面板（含"新建会话"按钮）、右侧 Skills 面板

#### Scenario: 发送并接收消息
- **WHEN** 用户输入文本并点击发送或按回车
- **THEN** 用户消息立即以右侧气泡展示；后端通过 `/chat` 返回结果后，Assistant 消息以左侧气泡展示

#### Scenario: 展示工具/Skill 调用
- **WHEN** Assistant 在一次回复中触发了 `tool_calls`
- **THEN** 消息区以可折叠的调用块展示"调用的工具名 + 参数 + 结果摘要"，默认折叠

### Requirement: 会话管理
系统 SHALL 允许用户在前端维护多个会话，并在会话间切换、清空或新建。

#### Scenario: 新建会话
- **WHEN** 用户点击"新建会话"
- **THEN** 前端调用 `POST /sessions` 获取新的 `session_id`，加入左侧列表，并自动切换为当前会话

#### Scenario: 清空当前会话
- **WHEN** 用户点击当前会话的"清空"按钮
- **THEN** 前端调用 `POST /sessions/{id}/clear`，当前消息流被清空

#### Scenario: 切换已有会话
- **WHEN** 用户在左侧列表点击某个会话
- **THEN** 该会话被设为当前会话，并（若本地缓存有历史）恢复展示历史消息

### Requirement: Skills 面板
系统 SHALL 向用户展示当前可用的 Skills，供用户了解 Agent 能力边界。

#### Scenario: 展示 Skill 列表
- **WHEN** 页面加载完成
- **THEN** 前端调用 `GET /skills` 并将返回的 name/description 渲染到右侧面板

### Requirement: 后端静态资源托管
系统 SHALL 在 FastAPI 应用上挂载 `frontend/` 为静态资源目录，并将根路径 `/` 指向前端入口。

#### Scenario: 访问根路径返回前端
- **WHEN** HTTP GET `/`
- **THEN** 返回 `frontend/index.html`，状态码 200

## MODIFIED Requirements

### Requirement: Web 服务启动
服务启动后，除原有 `/health`、`/chat`、`/sessions` 等 JSON 接口外，根路径 `/` SHALL 返回前端页面；原有 JSON 接口路径与行为保持兼容。

## REMOVED Requirements
无。
