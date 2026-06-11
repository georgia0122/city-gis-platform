// ========== AI 聊天核心逻辑 + 对话历史功能 ==========

var chatHistory = [];       // 当前对话的消息列表 (用于发送给后端)
var attachedFiles = [];     // 当前附件列表
var isChatSending = false;  // 发送锁
var currentSessionId = null; // 当前会话 ID
var LOCATION_STORAGE_KEY = 'geoweather_current_city';

window.attachedFiles = attachedFiles;

// ========== 工具函数 ==========
function formatTime(date) {
  if (!date) date = new Date();
  if (typeof date === 'string') date = new Date(date);
  var h = date.getHours().toString().padStart(2, '0');
  var m = date.getMinutes().toString().padStart(2, '0');
  return h + ':' + m;
}

function formatDate(dateStr) {
  if (!dateStr) return '今天';
  var d = new Date(dateStr);
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  var diff = (today - target) / (1000 * 60 * 60 * 24);
  if (diff === 0) return '今天';
  if (diff === 1) return '昨天';
  if (diff < 7) return Math.floor(diff) + '天前';
  return (d.getMonth() + 1) + '/' + d.getDate();
}

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function getStoredLocation() {
  try {
    var raw = localStorage.getItem(LOCATION_STORAGE_KEY);
    if (!raw) return null;
    var data = JSON.parse(raw);
    if (!data) return null;
    var lat = typeof data.lat === 'number' ? data.lat : parseFloat(data.lat);
    var lng = typeof data.lng === 'number' ? data.lng : parseFloat(data.lng);
    if (!isFinite(lat) || !isFinite(lng)) return null;
    return {
      lat: lat,
      lng: lng,
      name: data.name || '',
      city: data.city || ''
    };
  } catch (e) {
    console.warn('Failed to read stored location:', e);
    return null;
  }
}

// 简单 Markdown → HTML
function renderMarkdown(text) {
  if (!text) return '';
  var html = escapeHtml(text);
  // 代码块
  html = html.replace(/```([\s\S]*?)```/g, '<pre class="chat-code-block"><code>$1</code></pre>');
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="chat-inline-code">$1</code>');
  // 加粗
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // 列表项
  html = html.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  // 数字列表
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
  // 换行
  html = html.replace(/\n/g, '<br>');
  return html;
}

// ========== DOM 操作 ==========
function createMessageEl(role, content, timeStr, attachmentsList) {
  var msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message ' + role;

  var avatarSpan = document.createElement('span');
  avatarSpan.className = 'chat-msg-avatar ' + (role === 'assistant' ? 'chat-msg-avatar-ai' : 'chat-msg-avatar-user');
  avatarSpan.textContent = role === 'assistant' ? 'AI' : '我';

  var bodyDiv = document.createElement('div');
  bodyDiv.className = 'chat-msg-body';

  var bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'chat-bubble ' + role;
  bubbleDiv.innerHTML = renderMarkdown(content);

  bodyDiv.appendChild(bubbleDiv);

  // 附件显示
  if (attachmentsList && attachmentsList.length > 0) {
    attachmentsList.forEach(function(att) {
      var attDiv = document.createElement('div');
      attDiv.className = 'chat-attachment';
      if (att.type && att.type.startsWith('image/') && att.preview) {
        var img = document.createElement('img');
        img.className = 'chat-attachment-img';
        img.src = att.preview;
        img.alt = att.name || '图片';
        attDiv.appendChild(img);
      } else {
        var iconDiv = document.createElement('div');
        iconDiv.className = 'chat-attachment-icon';
        iconDiv.textContent = '📄';
        var infoDiv = document.createElement('div');
        infoDiv.className = 'chat-attachment-info';
        var nameDiv = document.createElement('div');
        nameDiv.className = 'chat-attachment-name';
        nameDiv.textContent = att.name || '文件';
        infoDiv.appendChild(nameDiv);
        attDiv.appendChild(iconDiv);
        attDiv.appendChild(infoDiv);
      }
      bodyDiv.appendChild(attDiv);
    });
  }

  var timeDiv = document.createElement('div');
  timeDiv.className = 'chat-time';
  timeDiv.textContent = timeStr || formatTime(new Date());
  bodyDiv.appendChild(timeDiv);

  msgDiv.appendChild(avatarSpan);
  msgDiv.appendChild(bodyDiv);
  return msgDiv;
}

function addUserMessage(content, attachmentsList) {
  var chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  var now = new Date();
  var timeStr = formatTime(now);

  // 附件摘要
  var attSummary = [];
  if (attachmentsList && attachmentsList.length > 0) {
    attachmentsList.forEach(function(a) {
      attSummary.push({ name: a.name, type: a.type || '', preview: a.preview || '' });
    });
  }

  var el = createMessageEl('user', content, timeStr, attSummary);
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // 记录到 chatHistory（用于 LLM 上下文）
  chatHistory.push({ role: 'user', content: content });

  // 保存到后端
  return saveMessageToSession('user', content, now.toISOString(), attSummary);
}

function addAssistantMessage(content) {
  var chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  var now = new Date();
  var timeStr = formatTime(now);

  var el = createMessageEl('assistant', content, timeStr);
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  chatHistory.push({ role: 'assistant', content: content });

  // 保存到后端
  return saveMessageToSession('assistant', content, now.toISOString(), []);
}

// 全局暴露给 file-analysis.js
window.addAssistantMessage = addAssistantMessage;
window.addUserMessage = addUserMessage;

// ========== 打字指示器 ==========
function showTypingIndicator() {
  var chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;
  hideTypingIndicator();
  var msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message assistant';
  msgDiv.id = 'typingIndicator';

  var avatar = document.createElement('span');
  avatar.className = 'chat-msg-avatar chat-msg-avatar-ai';
  avatar.textContent = 'AI';

  var body = document.createElement('div');
  body.className = 'chat-msg-body';
  var bubble = document.createElement('div');
  bubble.className = 'chat-bubble typing';
  bubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  body.appendChild(bubble);

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(body);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
  var indicator = document.getElementById('typingIndicator');
  if (indicator) indicator.remove();
}

window.showTypingIndicator = showTypingIndicator;
window.hideTypingIndicator = hideTypingIndicator;

// ========== 文件处理 ==========
function handleFileSelect(fileList) {
  if (!fileList || fileList.length === 0) return;

  for (var i = 0; i < fileList.length; i++) {
    var file = fileList[i];
    var fileObj = { file: file, name: file.name, type: file.type, size: file.size, preview: '' };

    // 图片预览
    if (file.type.startsWith('image/')) {
      (function(fo) {
        var reader = new FileReader();
        reader.onload = function(e) {
          fo.preview = e.target.result;
          renderFilePreview();
        };
        reader.readAsDataURL(file);
      })(fileObj);
    }

    attachedFiles.push(fileObj);
    window.attachedFiles = attachedFiles;
  }
  renderFilePreview();
}

function renderFilePreview() {
  var filePreview = document.getElementById('filePreview');
  if (!filePreview) return;

  filePreview.innerHTML = '';
  if (attachedFiles.length === 0) {
    filePreview.classList.remove('has-files');
    return;
  }
  filePreview.classList.add('has-files');

  attachedFiles.forEach(function(fo, idx) {
    var item = document.createElement('div');
    item.className = 'file-preview-item';

    if (fo.type && fo.type.startsWith('image/') && fo.preview) {
      var img = document.createElement('img');
      img.className = 'file-preview-img';
      img.src = fo.preview;
      img.alt = fo.name;
      item.appendChild(img);
    } else {
      var iconDiv = document.createElement('div');
      iconDiv.className = 'file-preview-icon';
      iconDiv.textContent = '📄';
      item.appendChild(iconDiv);
    }

    var info = document.createElement('div');
    info.className = 'file-preview-info';
    var nameDiv = document.createElement('div');
    nameDiv.className = 'file-preview-name';
    nameDiv.textContent = fo.name;
    var sizeDiv = document.createElement('div');
    sizeDiv.className = 'file-preview-size';
    sizeDiv.textContent = (fo.size / 1024).toFixed(1) + ' KB';
    info.appendChild(nameDiv);
    info.appendChild(sizeDiv);
    item.appendChild(info);

    var removeBtn = document.createElement('button');
    removeBtn.className = 'file-preview-remove';
    removeBtn.textContent = '×';
    removeBtn.onclick = function() {
      attachedFiles.splice(idx, 1);
      window.attachedFiles = attachedFiles;
      renderFilePreview();
    };
    item.appendChild(removeBtn);

    filePreview.appendChild(item);
  });
}

// ========== 发送消息 ==========
async function sendChatMessage(msg) {
  if (isChatSending) return;

  var chatInput = document.getElementById('chatInput');
  var chatSendBtn = document.getElementById('chatSendBtn');
  var chatStatus = document.getElementById('chatStatus');
  var filePreview = document.getElementById('filePreview');

  var userText = msg || '';
  if (!userText && attachedFiles.length === 0) return;

  isChatSending = true;
  if (chatSendBtn) chatSendBtn.disabled = true;
  if (chatInput) chatInput.disabled = true;
  if (chatStatus) chatStatus.textContent = 'AI 正在思考...';

  // 收集附件摘要
  var attList = attachedFiles.map(function(f) {
    return { name: f.name, type: f.type, preview: f.preview || '' };
  });

  // 显示用户消息
  var userSavePromise = Promise.resolve();
  if (userText) {
    userSavePromise = addUserMessage(userText, attList) || Promise.resolve();
  }

  showTypingIndicator();

  try {
    // 构建 FormData
    var formData = new FormData();
    formData.append('message', userText);
    formData.append('history', JSON.stringify(chatHistory));

    var storedLocation = getStoredLocation();
    if (storedLocation) {
      formData.append('lat', storedLocation.lat);
      formData.append('lng', storedLocation.lng);
      if (storedLocation.name || storedLocation.city) {
        formData.append('city', storedLocation.name || storedLocation.city);
      }
    }

    for (var i = 0; i < attachedFiles.length; i++) {
      formData.append('files', attachedFiles[i].file);
    }

    var resp = await fetch('/api/chat', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    var data = await resp.json();
    hideTypingIndicator();

    var assistantSavePromise = Promise.resolve();
    if (data.error) {
      assistantSavePromise = addAssistantMessage('❌ ' + data.error) || Promise.resolve();
    } else {
      assistantSavePromise = addAssistantMessage(data.reply) || Promise.resolve();
    }

    // 清空附件
    attachedFiles = [];
    window.attachedFiles = attachedFiles;
    if (filePreview) {
      filePreview.innerHTML = '';
      filePreview.classList.remove('has-files');
    }

    if (chatStatus) chatStatus.textContent = '随时为您解答各种问题';

    // 等待消息落库后再刷新侧边栏（避免首次加载为空）
    await Promise.all([userSavePromise, assistantSavePromise]);
    loadSessionList();

  } catch (err) {
    console.error('Chat error:', err);
    hideTypingIndicator();
    addAssistantMessage('❌ 网络错误，请稍后重试');
    if (chatStatus) chatStatus.textContent = '连接异常';
  } finally {
    isChatSending = false;
    if (chatSendBtn) chatSendBtn.disabled = false;
    if (chatInput) { chatInput.disabled = false; chatInput.focus(); }
  }
}

// ========== 对话历史管理 ==========

// 确保当前有会话 ID
async function ensureSession() {
  if (currentSessionId) return currentSessionId;
  try {
    var resp = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ title: '新对话' })
    });
    if (!resp.ok) {
      throw new Error('Failed to create session: ' + resp.status);
    }
    var data = await resp.json();
    if (!data || !data.id) {
      throw new Error('Invalid session response');
    }
    currentSessionId = data.id;
    return currentSessionId;
  } catch (e) {
    console.error('Failed to create session:', e);
    return null;
  }
}

// 保存消息到后端
async function saveMessageToSession(role, content, time, attachments) {
  try {
    var sid = await ensureSession();
    if (!sid) return;
    await fetch('/api/chat/sessions/' + sid + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        messages: [{
          role: role,
          content: content,
          time: time,
          attachments: attachments || []
        }]
      })
    });
  } catch (e) {
    console.error('Failed to save message:', e);
  }
}

// 加载会话列表
async function loadSessionList() {
  var listContainer = document.getElementById('chatSessionList');
  if (!listContainer) return;

  try {
    var resp = await fetch('/api/chat/sessions', { credentials: 'include' });
    if (!resp.ok) {
      listContainer.innerHTML = '<div class="chat-sidebar-empty">暂无历史对话</div>';
      return;
    }
    var data = await resp.json();
    var sessions = data.sessions || [];

    listContainer.innerHTML = '';

    if (sessions.length === 0) {
      var emptyDiv = document.createElement('div');
      emptyDiv.className = 'chat-sidebar-empty';
      emptyDiv.textContent = '暂无历史对话';
      listContainer.appendChild(emptyDiv);
      return;
    }

    sessions.forEach(function(session) {
      var item = document.createElement('div');
      item.className = 'chat-sidebar-item';
      if (session.id === currentSessionId) {
        item.classList.add('chat-sidebar-item-active');
      }
      item.dataset.sessionId = session.id;

      var titleDiv = document.createElement('div');
      titleDiv.className = 'chat-sidebar-item-title';
      titleDiv.textContent = session.title || '新对话';
      titleDiv.title = session.title || '新对话';

      var metaDiv = document.createElement('div');
      metaDiv.className = 'chat-sidebar-item-meta';

      var timeSpan = document.createElement('span');
      timeSpan.className = 'chat-sidebar-item-time';
      timeSpan.textContent = formatDate(session.updated_at);

      var countSpan = document.createElement('span');
      countSpan.className = 'chat-sidebar-item-count';
      countSpan.textContent = session.message_count + '条';

      metaDiv.appendChild(timeSpan);
      metaDiv.appendChild(countSpan);

      // 删除按钮
      var delBtn = document.createElement('button');
      delBtn.className = 'chat-sidebar-item-delete';
      delBtn.title = '删除此对话';
      delBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z"/></svg>';
      delBtn.onclick = function(e) {
        e.stopPropagation();
        deleteSession(session.id);
      };

      item.appendChild(titleDiv);
      item.appendChild(metaDiv);
      item.appendChild(delBtn);

      // 点击加载会话
      item.onclick = function() {
        loadSession(session.id);
      };

      listContainer.appendChild(item);
    });

  } catch (e) {
    console.error('Failed to load sessions:', e);
    if (listContainer) {
      listContainer.innerHTML = '<div class="chat-sidebar-empty">暂无历史对话</div>';
    }
  }
}

// 加载某个会话的全部消息
async function loadSession(sessionId) {
  try {
    var resp = await fetch('/api/chat/sessions/' + sessionId, { credentials: 'include' });
    var data = await resp.json();

    if (data.error) {
      console.error('Session load error:', data.error);
      return;
    }

    // 切换当前会话
    currentSessionId = sessionId;
    chatHistory = [];

    // 清空聊天区域
    var chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    chatMessages.innerHTML = '';

    // 渲染所有消息
    var messages = data.messages || [];
    if (messages.length === 0) {
      var welcome = createMessageEl('assistant', '您好！我是您的 AI 助手，有什么可以帮您的吗？\n\n我可以帮您：分析天气、出行建议、穿衣指南、分步出行规划等。');
      chatMessages.appendChild(welcome);
    } else {
      messages.forEach(function(msg) {
        var timeStr = msg.time ? formatTime(msg.time) : '';
        var el = createMessageEl(msg.role, msg.content, timeStr, msg.attachments);
        chatMessages.appendChild(el);
        chatHistory.push({ role: msg.role, content: msg.content });
      });
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 更新侧栏高亮
    updateSidebarActive(sessionId);

    // 更新标题
    var chatMainTitle = document.querySelector('.chat-main-title');
    if (chatMainTitle) {
      chatMainTitle.textContent = data.title || '智能AI助手';
    }

  } catch (e) {
    console.error('Failed to load session:', e);
  }
}

// 创建新会话
function createNewSession() {
  currentSessionId = null;
  chatHistory = [];

  // 清空聊天区域
  var chatMessages = document.getElementById('chatMessages');
  if (chatMessages) {
    chatMessages.innerHTML = '';
    var welcome = createMessageEl('assistant', '您好！我是您的 AI 助手，有什么可以帮您的吗？\n\n我可以帮您：分析天气、出行建议、穿衣指南、分步出行规划等。您也可以回到地图页选个位置，我能提供更精准的天气分析！');
    chatMessages.appendChild(welcome);
  }

  // 清除附件
  attachedFiles = [];
  window.attachedFiles = attachedFiles;
  var filePreview = document.getElementById('filePreview');
  if (filePreview) {
    filePreview.innerHTML = '';
    filePreview.classList.remove('has-files');
  }

  // 更新标题
  var chatMainTitle = document.querySelector('.chat-main-title');
  if (chatMainTitle) chatMainTitle.textContent = '智能AI助手';

  // 刷新侧栏
  updateSidebarActive(null);

  // 聚焦输入框
  var chatInput = document.getElementById('chatInput');
  if (chatInput) chatInput.focus();
}

// 删除会话
async function deleteSession(sessionId) {
  if (!confirm('确定删除此对话记录吗？')) return;

  try {
    await fetch('/api/chat/sessions/' + sessionId, { method: 'DELETE', credentials: 'include' });

    if (sessionId === currentSessionId) {
      createNewSession();
    }

    loadSessionList();
  } catch (e) {
    console.error('Failed to delete session:', e);
  }
}

// 更新侧栏高亮
function updateSidebarActive(activeId) {
  var items = document.querySelectorAll('.chat-sidebar-item');
  items.forEach(function(item) {
    if (item.dataset.sessionId === activeId) {
      item.classList.add('chat-sidebar-item-active');
    } else {
      item.classList.remove('chat-sidebar-item-active');
    }
  });
}

// ========== 侧栏展开/收起 ==========
function toggleChatSidebar() {
  var chatCard = document.querySelector('.chat-card');
  var chatSidebarToggle = document.getElementById('chatSidebarToggle');
  if (chatCard) {
    chatCard.classList.toggle('chat-sidebar-collapsed');
    var span = chatSidebarToggle && chatSidebarToggle.querySelector('span');
    if (span) {
      span.textContent = chatCard.classList.contains('chat-sidebar-collapsed') ? '展开' : '收起';
    }
    var svg = chatSidebarToggle && chatSidebarToggle.querySelector('svg');
    if (svg) {
      svg.style.transform = chatCard.classList.contains('chat-sidebar-collapsed') ? 'rotate(180deg)' : 'none';
    }
  }
}

// ========== 统一初始化 ==========
function initChatApp() {
  console.log('[chat.js] initChatApp start');

  // 发送按钮
  var chatSendBtn = document.getElementById('chatSendBtn');
  var chatInput = document.getElementById('chatInput');
  if (chatSendBtn) {
    chatSendBtn.onclick = function() {
      var msg = chatInput ? chatInput.value.trim() : '';
      if (msg || attachedFiles.length > 0) {
        if (chatInput) chatInput.value = '';
        sendChatMessage(msg);
      }
    };
  }

  // 回车发送
  if (chatInput) {
    chatInput.onkeydown = function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (chatSendBtn) chatSendBtn.click();
      }
    };
  }

  // 清空按钮 → 新建对话
  var chatClearBtn = document.getElementById('chatClearBtn');
  if (chatClearBtn) {
    chatClearBtn.onclick = function() {
      createNewSession();
    };
  }

  // 新建对话按钮
  var newChatBtn = document.getElementById('newChatBtn');
  if (newChatBtn) {
    newChatBtn.onclick = function() {
      createNewSession();
    };
  }

  // 项目按钮
  var projectBtn = document.getElementById('projectBtn');
  if (projectBtn) {
    projectBtn.onclick = function() { alert('项目功能开发中...'); };
  }

  // 图片按钮
  var imageBtn = document.getElementById('imageBtn');
  var imageInput = document.getElementById('imageInput');
  if (imageBtn) {
    imageBtn.onclick = function() { if (imageInput) imageInput.click(); };
  }
  if (imageInput) {
    imageInput.onchange = function(e) {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelect(e.target.files);
        e.target.value = '';
      }
    };
  }

  // 文件按钮
  var fileBtn = document.getElementById('fileBtn');
  var fileInput = document.getElementById('fileInput');
  if (fileBtn) {
    fileBtn.onclick = function() { if (fileInput) fileInput.click(); };
  }
  if (fileInput) {
    fileInput.onchange = function(e) {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelect(e.target.files);
        e.target.value = '';
      }
    };
  }

  // 分析按钮
  var analyzeBtn = document.getElementById('analyzeBtn');
  if (analyzeBtn) {
    analyzeBtn.onclick = function() {
      if (window.fileAnalysis && typeof window.fileAnalysis.analyzeFiles === 'function') {
        window.fileAnalysis.analyzeFiles();
      } else {
        alert('请先上传文件');
      }
    };
  }

  // 快捷卡片
  var quickActions = document.getElementById('chatQuickActions');
  if (quickActions) {
    quickActions.onclick = function(e) {
      var btn = e.target.closest('.quick-card');
      if (btn && btn.dataset.msg) {
        sendChatMessage(btn.dataset.msg);
      }
    };
  }

  // 侧栏切换
  var chatSidebarToggle = document.getElementById('chatSidebarToggle');
  var chatSidebarExpandBtn = document.getElementById('chatSidebarExpandBtn');
  if (chatSidebarToggle) chatSidebarToggle.onclick = toggleChatSidebar;
  if (chatSidebarExpandBtn) chatSidebarExpandBtn.onclick = toggleChatSidebar;

  // 加载历史会话列表
  loadSessionList();

  console.log('[chat.js] initChatApp done');
}

// ========== 启动 ==========
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatApp);
} else {
  initChatApp();
}
