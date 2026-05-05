# Tasks

- [x] Task 1：后端补齐前端所需接口与静态托管
  - [x] SubTask 1.1：在 `agent_service.py` 新增 `get_history(session_id)` 方法，返回该会话的 `messages`（直接复用 `SessionStore.get_messages`，不改动存储层）
  - [x] SubTask 1.2：在 `server.py` 新增 `GET /sessions/{session_id}/messages` 路由，返回历史消息（供前端切换会话后回放）
  - [x] SubTask 1.3：在 `server.py` 使用 `StaticFiles` 将 `frontend/` 挂载为静态资源，根路径 `/` 指向 `frontend/index.html`
  - [x] SubTask 1.4：为保证本机浏览器访问顺畅，酌情添加 `CORSMiddleware`（allow_origins 仅含 `http://127.0.0.1:8000` 与 `http://localhost:8000`）

- [x] Task 2：实现前端对话页面
  - [x] SubTask 2.1：创建 `frontend/index.html`：三栏布局（左会话列表 / 中消息流+输入 / 右 Skills 面板），引入 `styles.css` 与 `app.js`
  - [x] SubTask 2.2：创建 `frontend/styles.css`：主流 Agent 风格（深浅色基调、消息气泡左右区分、工具调用折叠块、响应式）
  - [x] SubTask 2.3：创建 `frontend/app.js`：封装 API 调用（`POST /sessions`、`POST /chat`、`POST /sessions/{id}/clear`、`GET /skills`、`GET /sessions/{id}/messages`）与渲染逻辑
  - [x] SubTask 2.4：实现会话管理：新建 / 切换 / 清空，会话列表在 `localStorage` 持久化
  - [x] SubTask 2.5：实现消息交互：Enter 发送（Shift+Enter 换行）、发送时禁用按钮、加载中 loading 提示、失败 toast
  - [x] SubTask 2.6：实现工具/Skill 调用的折叠展示（从 `/chat` 返回的 messages 中识别 `role=assistant` 的 `tool_calls` 与 `role=tool` 的结果进行配对渲染）
  - [x] SubTask 2.7：实现 Skills 面板：页面加载时拉取 `GET /skills` 并渲染 name + description

- [x] Task 3：文档更新与本地验证
  - [x] SubTask 3.1：更新 `README.md`，补充"启动后访问 http://127.0.0.1:8000/ 使用前端对话页面"说明
  - [x] SubTask 3.2：本地跑通：启动 `uvicorn server:app --host 127.0.0.1 --port 8000`，在浏览器验证 `新建会话 / 发消息 / 清空 / 切换 / 展示 Skills / 工具调用折叠块` 全链路

# Task Dependencies
- Task 2 依赖 Task 1（前端调用新路由）
- Task 3 依赖 Task 1、Task 2
