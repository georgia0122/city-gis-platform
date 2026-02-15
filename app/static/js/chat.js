/**
 * AI 智能对话页专用脚本（独立页，无地图）
 * 支持：发送消息、清空、快捷卡片、侧栏收起/展开、文件上传
 */
let chatHistory = [];
let isChatSending = false;
let attachedFiles = [];  // 存储待上传的文件

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const chatClearBtn = document.getElementById("chatClearBtn");
const chatStatus = document.getElementById("chatStatus");
const fileInput = document.getElementById("fileInput");
const imageInput = document.getElementById("imageInput");
const filePreview = document.getElementById("filePreview");
const projectBtn = document.getElementById("projectBtn");
const imageBtn = document.getElementById("imageBtn");
const fileBtn = document.getElementById("fileBtn");

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

function createMessageEl(role, content, files = []) {
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

  // 如果有文件附件，显示文件预览
  if (files && files.length > 0) {
    files.forEach(file => {
      const attachment = document.createElement('div');
      attachment.className = 'chat-attachment';
      
      if (file.type && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const img = document.createElement('img');
          img.src = e.target.result;
          img.className = 'chat-attachment-img';
          img.onclick = function() { window.open(e.target.result, '_blank'); };
          attachment.appendChild(img);
        };
        reader.readAsDataURL(file);
      } else {
        const icon = document.createElement('div');
        icon.className = 'chat-attachment-icon';
        icon.textContent = '📄';
        attachment.appendChild(icon);
        
        const info = document.createElement('div');
        info.className = 'chat-attachment-info';
        info.innerHTML = `<div class="chat-attachment-name">${escapeHtml(file.name)}</div>`;
        attachment.appendChild(info);
      }
      
      bubble.appendChild(attachment);
    });
  }

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

function addUserMessage(content, files = []) {
  chatHistory.push({ role: "user", content });
  const el = createMessageEl("user", content, files);
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
  if ((!message || message.trim() === '') && attachedFiles.length === 0) return;
  if (isChatSending) return;

  isChatSending = true;
  chatSendBtn.disabled = true;
  chatInput.disabled = true;
  if (chatStatus) chatStatus.textContent = "思考中...";

  // 显示用户消息（包含文件附件）
  const userMessageContent = message || '(发送了文件)';
  addUserMessage(userMessageContent, attachedFiles.map(f => f.file));
  showTypingIndicator();

  try {
    const formData = new FormData();
    formData.append('message', message || '请分析这些文件内容');
    formData.append('history', JSON.stringify(chatHistory.slice(0, -1)));

    // 添加文件到 FormData
    for (let fileObj of attachedFiles) {
      formData.append('files', fileObj.file);
    }

    const resp = await fetch("/api/chat", {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    hideTypingIndicator();

    if (data.error) {
      addAssistantMessage("❌ " + data.error);
    } else {
      addAssistantMessage(data.reply);
    }

    // 清空已发送的文件
    attachedFiles = [];
    filePreview.innerHTML = '';
    filePreview.classList.remove('has-files');

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
    if (msg || attachedFiles.length > 0) {
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
      if (msg || attachedFiles.length > 0) {
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
var chatSidebarExpandBtn = document.getElementById("chatSidebarExpandBtn");
var chatCard = document.querySelector(".chat-card");

function toggleChatSidebar() {
  if (chatCard) {
    chatCard.classList.toggle("chat-sidebar-collapsed");
    var span = chatSidebarToggle && chatSidebarToggle.querySelector("span");
    if (span) {
      span.textContent = chatCard.classList.contains("chat-sidebar-collapsed") ? "展开" : "收起";
    }
    var svg = chatSidebarToggle && chatSidebarToggle.querySelector("svg");
    if (svg) {
      svg.style.transform = chatCard.classList.contains("chat-sidebar-collapsed") ? "rotate(180deg)" : "none";
    }
  }
}

if (chatSidebarToggle && chatCard) {
  chatSidebarToggle.addEventListener("click", toggleChatSidebar);
}

if (chatSidebarExpandBtn && chatCard) {
  chatSidebarExpandBtn.addEventListener("click", toggleChatSidebar);
}
// ========== 文件上传功能 ==========

// 文件大小格式化
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// 判断是否为图片
function isImageFile(file) {
  return file.type.startsWith('image/');
}

// 添加文件到预览区
function addFileToPreview(file) {
  const item = document.createElement('div');
  item.className = 'file-preview-item';
  item.dataset.fileId = Date.now() + '_' + Math.random();

  if (isImageFile(file)) {
    const reader = new FileReader();
    reader.onload = function(e) {
      const img = document.createElement('img');
      img.src = e.target.result;
      img.className = 'file-preview-img';
      item.insertBefore(img, item.firstChild);
    };
    reader.readAsDataURL(file);
  } else {
    const icon = document.createElement('div');
    icon.className = 'file-preview-icon';
    icon.textContent = '📄';
    item.appendChild(icon);
  }

  const info = document.createElement('div');
  info.className = 'file-preview-info';
  info.innerHTML = `
    <div class="file-preview-name">${escapeHtml(file.name)}</div>
    <div class="file-preview-size">${formatFileSize(file.size)}</div>
  `;
  item.appendChild(info);

  const removeBtn = document.createElement('button');
  removeBtn.className = 'file-preview-remove';
  removeBtn.textContent = '×';
  removeBtn.onclick = function() {
    const fileId = item.dataset.fileId;
    attachedFiles = attachedFiles.filter(f => f.id !== fileId);
    item.remove();
    if (attachedFiles.length === 0) {
      filePreview.classList.remove('has-files');
    }
  };
  item.appendChild(removeBtn);

  filePreview.appendChild(item);
  filePreview.classList.add('has-files');
  
  return item.dataset.fileId;
}

// 处理文件选择
function handleFileSelect(files) {
  for (let file of files) {
    // 限制文件大小 10MB
    if (file.size > 10 * 1024 * 1024) {
      alert(`文件 ${file.name} 超过 10MB 限制`);
      continue;
    }
    
    const fileId = addFileToPreview(file);
    attachedFiles.push({ id: fileId, file: file });
  }
}

// 按钮点击事件
if (projectBtn) {
  projectBtn.addEventListener('click', function() {
    // 项目功能暂未实现
    alert('项目功能开发中...');
  });
}

if (imageBtn) {
  imageBtn.addEventListener('click', function() {
    imageInput.click();
  });
}

if (fileBtn) {
  fileBtn.addEventListener('click', function() {
    fileInput.click();
  });
}

if (imageInput) {
  imageInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files);
      e.target.value = '';
    }
  });
}

if (fileInput) {
  fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files);
      e.target.value = '';
    }
  });
}