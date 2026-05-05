/* ===================== MyAgent 前端脚本 =====================
 * 纯原生 JS，无任何框架依赖。
 * 负责：
 *   - 会话管理（新建 / 切换 / 清空 / localStorage 持久化）
 *   - 消息收发（调用 /chat）
 *   - 历史回放（切换会话时调用 /sessions/{id}/messages）
 *   - Skills 面板渲染（/skills）
 *   - 工具调用折叠块展示
 * ========================================================= */

const LS_KEY = "myagent.sessions.v1";
const LS_CURRENT = "myagent.current_session.v1";

const state = {
  sessions: [],        // [{ id, title, updatedAt }]
  currentId: null,
  isSending: false,
  lastUserInput: "",   // 用于在刷新时渲染
};

// -------- DOM --------
const el = {
  sessionList: document.getElementById("session-list"),
  btnNew: document.getElementById("btn-new-session"),
  btnClear: document.getElementById("btn-clear-session"),
  btnSend: document.getElementById("btn-send"),
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("empty-state"),
  input: document.getElementById("input"),
  currentLabel: document.getElementById("current-session-label"),
  skillsList: document.getElementById("skills-list"),
  toast: document.getElementById("toast"),
};

// -------- Utils --------
function showToast(text, durationMs = 2800) {
  el.toast.textContent = text;
  el.toast.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.toast.classList.add("hidden"), durationMs);
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function shortId(id) {
  return id ? id.slice(0, 8) : "";
}

function saveSessions() {
  localStorage.setItem(LS_KEY, JSON.stringify(state.sessions));
  if (state.currentId) {
    localStorage.setItem(LS_CURRENT, state.currentId);
  }
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) state.sessions = JSON.parse(raw) || [];
  } catch (_) {
    state.sessions = [];
  }
  state.currentId = localStorage.getItem(LS_CURRENT) || null;
}

// -------- API --------
async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const j = await resp.json();
      if (j.detail) detail = j.detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return resp.json();
}

const Api = {
  createSession: () => api("/sessions", { method: "POST" }),
  chat: (session_id, message) =>
    api("/chat", { method: "POST", body: JSON.stringify({ session_id, message }) }),
  clearSession: (id) => api(`/sessions/${id}/clear`, { method: "POST" }),
  getMessages: (id) => api(`/sessions/${id}/messages`),
  getSkills: () => api("/skills"),
};

// -------- Session Management --------
async function createNewSession() {
  try {
    const { session_id } = await Api.createSession();
    const s = {
      id: session_id,
      title: `会话 ${shortId(session_id)}`,
      updatedAt: Date.now(),
    };
    state.sessions.unshift(s);
    state.currentId = session_id;
    saveSessions();
    renderSessionList();
    renderCurrentLabel();
    clearMessagesView();
    return s;
  } catch (e) {
    showToast(`新建会话失败: ${e.message}`);
    throw e;
  }
}

async function switchSession(id) {
  if (state.currentId === id) return;
  state.currentId = id;
  saveSessions();
  renderSessionList();
  renderCurrentLabel();
  clearMessagesView();
  // 拉取历史
  try {
    const { messages } = await Api.getMessages(id);
    renderHistoryMessages(messages || []);
  } catch (e) {
    showToast(`加载历史失败: ${e.message}`);
  }
}

async function clearCurrentSession() {
  if (!state.currentId) return;
  try {
    await Api.clearSession(state.currentId);
    clearMessagesView();
    showToast("会话已清空");
  } catch (e) {
    showToast(`清空失败: ${e.message}`);
  }
}

// -------- Rendering --------
function renderSessionList() {
  el.sessionList.innerHTML = "";
  if (state.sessions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "skill-empty";
    empty.textContent = "暂无会话";
    el.sessionList.appendChild(empty);
    return;
  }
  for (const s of state.sessions) {
    const item = document.createElement("div");
    item.className = "session-item" + (s.id === state.currentId ? " active" : "");
    item.title = s.id;
    item.innerHTML = `<span class="dot"></span><span>${escapeHtml(s.title)}</span>`;
    item.addEventListener("click", () => switchSession(s.id));
    el.sessionList.appendChild(item);
  }
}

function renderCurrentLabel() {
  if (state.currentId) {
    el.currentLabel.textContent = `session: ${shortId(state.currentId)}`;
  } else {
    el.currentLabel.textContent = "未选择会话";
  }
}

function clearMessagesView() {
  el.messages.innerHTML = "";
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.innerHTML = `
    <div class="empty-title">开始一段对话</div>
    <div class="empty-sub">在下方输入框里输入你的问题，Agent 将调用工具与技能协助你。</div>
  `;
  el.messages.appendChild(empty);
}

function removeEmptyState() {
  const empty = el.messages.querySelector(".empty-state");
  if (empty) empty.remove();
}

function appendUserMessage(text) {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `
    <div class="msg-avatar user">U</div>
    <div class="msg-bubble"></div>
  `;
  row.querySelector(".msg-bubble").textContent = text;
  el.messages.appendChild(row);
  scrollToBottom();
}

function appendAssistantMessage(text) {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-avatar assistant">A</div>
    <div class="msg-bubble"></div>
  `;
  row.querySelector(".msg-bubble").textContent = text;
  el.messages.appendChild(row);
  scrollToBottom();
  return row;
}

function appendLoadingMessage() {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.dataset.loading = "1";
  row.innerHTML = `
    <div class="msg-avatar assistant">A</div>
    <div class="msg-bubble">
      <span class="loading-dots"><span></span><span></span><span></span></span>
    </div>
  `;
  el.messages.appendChild(row);
  scrollToBottom();
  return row;
}

function appendToolCallBlock(toolName, args, resultText) {
  removeEmptyState();
  const details = document.createElement("details");
  details.className = "tool-call";
  const argsStr = typeof args === "string" ? args : JSON.stringify(args, null, 2);
  details.innerHTML = `
    <summary>
      <span>调用工具</span>
      <span class="tool-name">${escapeHtml(toolName || "unknown")}</span>
    </summary>
    <div class="tool-body">
      <span class="label">参数</span>
      <div>${escapeHtml(argsStr || "{}")}</div>
      <span class="label">结果</span>
      <div>${escapeHtml(resultText || "")}</div>
    </div>
  `;
  el.messages.appendChild(details);
  scrollToBottom();
}

function scrollToBottom() {
  el.messages.scrollTop = el.messages.scrollHeight;
}

/**
 * 基于后端返回的完整 messages 渲染历史（含 tool_calls 与 tool 结果配对）
 */
function renderHistoryMessages(messages) {
  el.messages.innerHTML = "";
  if (!messages || messages.length === 0) {
    clearMessagesView();
    return;
  }

  // 建立 tool_call_id -> 结果 的映射
  const toolResults = {};
  for (const m of messages) {
    if (m.role === "tool" && m.tool_call_id) {
      toolResults[m.tool_call_id] = m.content || "";
    }
  }

  for (const m of messages) {
    if (m.role === "system") continue;
    if (m.role === "user") {
      if (m.content) appendUserMessage(m.content);
    } else if (m.role === "assistant") {
      if (m.tool_calls && m.tool_calls.length > 0) {
        for (const tc of m.tool_calls) {
          const fn = tc.function || {};
          const name = fn.name;
          const args = fn.arguments;
          const result = toolResults[tc.id] || "";
          appendToolCallBlock(name, args, result);
        }
      }
      if (m.content) appendAssistantMessage(m.content);
    }
    // role === "tool" 已在 tool_call 块中展示，无需单独渲染
  }
  scrollToBottom();
}

// -------- Sending --------
async function sendMessage() {
  if (state.isSending) return;
  const text = el.input.value.trim();
  if (!text) return;
  if (!state.currentId) {
    try { await createNewSession(); } catch (_) { return; }
  }

  state.isSending = true;
  el.btnSend.disabled = true;
  el.input.disabled = true;

  appendUserMessage(text);
  el.input.value = "";
  autoResize();

  const loadingRow = appendLoadingMessage();

  try {
    // 发送前记录发送时历史长度，以便识别本轮新增的 tool_calls
    const before = await Api.getMessages(state.currentId);
    const beforeLen = (before.messages || []).length;

    const { reply } = await Api.chat(state.currentId, text);

    // 移除 loading，拉取最新 history，渲染本轮新增部分
    loadingRow.remove();

    const after = await Api.getMessages(state.currentId);
    const newMessages = (after.messages || []).slice(beforeLen);
    renderRoundMessages(newMessages, reply);

    // 更新会话标题（首条消息做截断展示）
    updateSessionTitleIfEmpty(text);
  } catch (e) {
    loadingRow.remove();
    appendAssistantMessage(`(发送失败) ${e.message}`);
    showToast(`发送失败: ${e.message}`);
  } finally {
    state.isSending = false;
    el.btnSend.disabled = false;
    el.input.disabled = false;
    el.input.focus();
  }
}

/**
 * 渲染本轮新增消息（user 已在前端预渲染过，不重复）。
 * 展示 assistant tool_calls 折叠块和最终 assistant 文本。
 */
function renderRoundMessages(newMessages, fallbackReply) {
  const toolResults = {};
  for (const m of newMessages) {
    if (m.role === "tool" && m.tool_call_id) {
      toolResults[m.tool_call_id] = m.content || "";
    }
  }

  let lastAssistantText = null;
  for (const m of newMessages) {
    if (m.role === "user") continue; // 已在前端预渲染
    if (m.role === "assistant") {
      if (m.tool_calls && m.tool_calls.length > 0) {
        for (const tc of m.tool_calls) {
          const fn = tc.function || {};
          appendToolCallBlock(fn.name, fn.arguments, toolResults[tc.id] || "");
        }
      }
      if (m.content) lastAssistantText = m.content;
    }
  }

  const finalText = lastAssistantText || fallbackReply || "";
  if (finalText) appendAssistantMessage(finalText);
}

function updateSessionTitleIfEmpty(firstUserText) {
  const s = state.sessions.find((x) => x.id === state.currentId);
  if (!s) return;
  if (s.title && !s.title.startsWith("会话 ")) return; // 已改过标题则不动
  s.title = firstUserText.length > 20 ? firstUserText.slice(0, 20) + "…" : firstUserText;
  s.updatedAt = Date.now();
  saveSessions();
  renderSessionList();
}

// -------- Skills --------
async function loadSkills() {
  try {
    const { skills } = await Api.getSkills();
    el.skillsList.innerHTML = "";
    if (!skills || skills.length === 0) {
      const empty = document.createElement("div");
      empty.className = "skill-empty";
      empty.textContent = "暂无可用技能";
      el.skillsList.appendChild(empty);
      return;
    }
    for (const sk of skills) {
      const item = document.createElement("div");
      item.className = "skill-item";
      item.innerHTML = `
        <div class="skill-name">${escapeHtml(sk.name)}</div>
        <div class="skill-desc">${escapeHtml(sk.description || "")}</div>
      `;
      el.skillsList.appendChild(item);
    }
  } catch (e) {
    const err = document.createElement("div");
    err.className = "skill-empty";
    err.textContent = `加载技能失败: ${e.message}`;
    el.skillsList.innerHTML = "";
    el.skillsList.appendChild(err);
  }
}

// -------- Input Auto-resize --------
function autoResize() {
  el.input.style.height = "auto";
  el.input.style.height = Math.min(el.input.scrollHeight, 200) + "px";
}

// -------- Events --------
function bindEvents() {
  el.btnNew.addEventListener("click", () => createNewSession());
  el.btnClear.addEventListener("click", () => clearCurrentSession());
  el.btnSend.addEventListener("click", () => sendMessage());

  el.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendMessage();
    }
  });
  el.input.addEventListener("input", autoResize);
}

// -------- Init --------
async function init() {
  bindEvents();
  loadSessions();

  if (state.sessions.length === 0 || !state.currentId) {
    // 没有任何本地会话，自动新建
    await createNewSession();
  } else {
    renderSessionList();
    renderCurrentLabel();
    // 回放当前会话历史
    try {
      const { messages } = await Api.getMessages(state.currentId);
      renderHistoryMessages(messages || []);
    } catch (e) {
      // 后端可能没有这个 session（重启后内存清空），重新新建一个
      console.warn("load history failed, creating new:", e.message);
      state.sessions = [];
      state.currentId = null;
      saveSessions();
      await createNewSession();
    }
  }

  loadSkills();
  el.input.focus();
}

init();
