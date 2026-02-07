/**
 * AI 智能对话页专用脚本（独立页，无地图）
 * 支持：发送消息、清空、快捷卡片、侧栏收起/展开
 */
let chatHistory = [];
let isChatSending = false;

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const chatClearBtn = document.getElementById("chatClearBtn");
const chatStatus = document.getElementById("chatStatus");

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatMessageContent(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\n/g, "<br>");
  return html;
}

function formatTimeLabel() {
  const now = new Date();
  return "今天 " + now.getHours().toString().padStart(2, "0") + ":" + now.getMinutes().toString().padStart(2, "0");
}

function createMessageEl(role, content) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-message ${role}`;

  const avatar = document.createElement("span");
  avatar.className = role === "user" ? "chat-msg-avatar chat-msg-avatar-user" : "chat-msg-avatar chat-msg-avatar-ai";
  avatar.textContent = role === "user" ? "我" : "AI";

  const body = document.createElement("div");
  body.className = "chat-msg-body";

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = formatMessageContent(content);

  const time = document.createElement("div");
  time.className = "chat-time";
  time.textContent = formatTimeLabel();

  body.appendChild(bubble);
  body.appendChild(time);
  wrapper.appendChild(avatar);
  wrapper.appendChild(body);
  return wrapper;
}

function createTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "chat-message assistant";
  wrapper.id = "typingIndicator";

  const avatar = document.createElement("span");
  avatar.className = "chat-msg-avatar chat-msg-avatar-ai";
  avatar.textContent = "AI";

  const body = document.createElement("div");
  body.className = "chat-msg-body";

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble assistant typing";
  bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

  body.appendChild(bubble);
  wrapper.appendChild(avatar);
  wrapper.appendChild(body);
  return wrapper;
}

function scrollChatToBottom() {
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addUserMessage(content) {
  chatHistory.push({ role: "user", content });
  const el = createMessageEl("user", content);
  chatMessages.appendChild(el);
  scrollChatToBottom();
}

function addAssistantMessage(content) {
  chatHistory.push({ role: "assistant", content });
  const el = createMessageEl("assistant", content);
  chatMessages.appendChild(el);
  scrollChatToBottom();
}

function showTypingIndicator() {
  const existing = document.getElementById("typingIndicator");
  if (existing) existing.remove();
  chatMessages.appendChild(createTypingIndicator());
  scrollChatToBottom();
}

function hideTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

async function sendChatMessage(message) {
  if (!message || isChatSending) return;

  isChatSending = true;
  chatSendBtn.disabled = true;
  chatInput.disabled = true;
  if (chatStatus) chatStatus.textContent = "思考中...";

  addUserMessage(message);
  showTypingIndicator();

  try {
    const body = { message, history: chatHistory.slice(0, -1) };
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    hideTypingIndicator();

    if (data.error) {
      addAssistantMessage("❌ " + data.error);
    } else {
      addAssistantMessage(data.reply);
    }

    if (chatStatus) chatStatus.textContent = "随时为您解答各种问题";
  } catch (err) {
    console.error("Chat error:", err);
    hideTypingIndicator();
    addAssistantMessage("❌ 网络错误，请稍后重试");
    if (chatStatus) chatStatus.textContent = "连接异常";
  } finally {
    isChatSending = false;
    chatSendBtn.disabled = false;
    chatInput.disabled = false;
    if (chatInput) chatInput.focus();
  }
}

if (chatSendBtn) {
  chatSendBtn.addEventListener("click", function () {
    const msg = chatInput.value.trim();
    if (msg) {
      chatInput.value = "";
      sendChatMessage(msg);
    }
  });
}

if (chatInput) {
  chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const msg = chatInput.value.trim();
      if (msg) {
        chatInput.value = "";
        sendChatMessage(msg);
      }
    }
  });
}

if (chatClearBtn) {
  chatClearBtn.addEventListener("click", function () {
    chatHistory = [];
    chatMessages.innerHTML = "";
    const welcome = createMessageEl(
      "assistant",
      "对话已清空 🧹\n\n您好！我是您的 AI 助手，有什么可以帮您的吗？"
    );
    chatMessages.appendChild(welcome);
    if (chatStatus) chatStatus.textContent = "随时为您解答各种问题";
  });
}

document.querySelectorAll(".quick-card, .quick-action-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const msg = btn.dataset.msg;
    if (msg) sendChatMessage(msg);
  });
});

// 对话历史侧栏收起/展开
var chatSidebarToggle = document.getElementById("chatSidebarToggle");
var chatCard = document.querySelector(".chat-card");
if (chatSidebarToggle && chatCard) {
  chatSidebarToggle.addEventListener("click", function () {
    chatCard.classList.toggle("chat-sidebar-collapsed");
    var span = chatSidebarToggle.querySelector("span");
    if (span) {
      span.textContent = chatCard.classList.contains("chat-sidebar-collapsed") ? "展开" : "收起";
    }
    var svg = chatSidebarToggle.querySelector("svg");
    if (svg) {
      svg.style.transform = chatCard.classList.contains("chat-sidebar-collapsed") ? "rotate(180deg)" : "none";
    }
  });
}
