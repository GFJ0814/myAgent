# Checklist

## 后端
- [x] `agent_service.py` 提供 `get_history(session_id)` 方法，返回指定会话的 messages
- [x] `server.py` 提供 `GET /sessions/{session_id}/messages` 路由，返回历史消息 JSON
- [x] `server.py` 使用 `StaticFiles` 挂载 `frontend/` 为静态资源目录
- [x] 根路径 `GET /` 返回 `frontend/index.html`，状态码 200
- [x] 原有 `/health`、`/chat`、`/sessions`、`POST /sessions/{id}/clear`、`GET /skills` 路由行为不受影响

## 前端结构
- [x] 存在 `frontend/index.html`、`frontend/app.js`、`frontend/styles.css` 三个文件
- [x] 页面呈现三栏布局：左侧会话列表、中间消息流+输入框、右侧 Skills 面板
- [x] 无第三方前端构建工具依赖（纯 HTML/CSS/JS）

## 前端功能
- [x] 首次进入页面自动创建默认会话或加载上次的当前会话
- [x] "新建会话"按钮可调用 `POST /sessions`，新会话出现在列表并被设为当前会话
- [x] 切换会话时加载并渲染该会话的历史消息
- [x] "清空"按钮触发 `POST /sessions/{id}/clear`，当前消息区被清空
- [x] 输入框支持 Enter 发送、Shift+Enter 换行；发送中按钮禁用并展示 loading
- [x] 用户消息展示为右侧气泡，Assistant 消息展示为左侧气泡
- [x] 当 Assistant 回复包含 `tool_calls` 时，前端以可折叠块展示"工具名/参数/结果"，默认折叠
- [x] 页面加载时拉取 `GET /skills`，在右侧面板展示 name 与 description
- [x] 会话列表在 `localStorage` 持久化，刷新后不丢失

## 文档与验证
- [x] `README.md` 更新启动说明，指引访问 `http://127.0.0.1:8000/`
- [x] 本地启动 `uvicorn server:app` 后浏览器可完整走完：新建→发消息→收到回复→触发工具调用并可折叠查看→清空→切换→展示 Skills
