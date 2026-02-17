c i = 0; i < attachedFiles.length; i++) {
      formData.append('files', attachedFiles[i].file);
    }

    var resp = await fetch("/api/chat", {
      method: "POST",
      body: formData,
    });
    var data = await resp.json();
    hideTypingIndicator();

    if (data.error) {
      addAssistantMessage("❌ " + data.error);
    } else {
      addAssistantMessage(data.reply);
    }

    // 清空已发送的文件
    attachedFiles = [];
    window.attachedFiles = attachedFiles;
    if (filePreview) {
      filePreview.innerHTML = '';
      filePreview.classList.remove('has-files');
    }

    if (chatStatus) chatStatus.textContent = "随时为您解答各种问题";
  } catch (err) {
    console.error("Chat error:", err);
    hideTypingIndicator();
    addAssistantMessage("❌ 网络错误，请稍后重试");
    if (chatStatus) chatStatus.textContent = "连接异常";
  } finally {
    isChatSending = false;
    if (chatSendBtn) chatSendBtn.disabled = false;
    if (chatInput) { chatInput.disabled = false; chatInput.focus(); }
  }
}

// ========== 侧栏展开/收起 ==========
function toggleChatSidebar() {
  var chatCard = document.querySelector(".chat-card");
  var chatSidebarToggle = document.getElementById("chatSidebarToggle");
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

// ========== 统一初始化（只绑定一次） ==========
function initChatApp() {
  console.log('[chat.js] initChatApp start');

  // 发送按钮
  var chatSendBtn = document.getElementById("chatSendBtn");
  var chatInput = document.getElementById("chatInput");
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

  // 清空按钮
  var chatClearBtn = document.getElementById("chatClearBtn");
  if (chatClearBtn) {
    chatClearBtn.onclick = function() {
      chatHistory = [];
      var chatMessages = document.getElementById("chatMessages");
      if (chatMessages) {
        chatMessages.innerHTML = '';
        var welcome = createMessageEl("assistant", "对话已清空 🧹\n\n您好！我是您的 AI 助手，有什么可以帮您的吗？");
        chatMessages.appendChild(welcome);
      }
    };
  }

  // 项目按钮
  var projectBtn = document.getElementById("projectBtn");
  if (projectBtn) {
    projectBtn.onclick = function() { alert('项目功能开发中...'); };
  }

  // 图片按钮
  var imageBtn = document.getElementById("imageBtn");
  var imageInput = document.getElementById("imageInput");
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
  var fileBtn = document.getElementById("fileBtn");
  var fileInput = document.getElementById("fileInput");
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
  var analyzeBtn = document.getElementById("analyzeBtn");
  if (analyzeBtn) {
    analyzeBtn.onclick = function() {
      if (window.fileAnalysis && typeof window.fileAnalysis.analyzeFiles === 'function') {
        window.fileAnalysis.analyzeFiles();
      } else {
        alert('请先上传文件');
      }
    };
  }

  // 快捷卡片（事件委托）
  var quickActions = document.getElementById("chatQuickActions");
  if (quickActions) {
    quickActions.onclick = function(e) {
      var btn = e.target.closest(".quick-card");
      if (btn && btn.dataset.msg) {
        sendChatMessage(btn.dataset.msg);
      }
    };
  }

  // 侧栏
  var chatSidebarToggle = document.getElementById("chatSidebarToggle");
  var chatSidebarExpandBtn = document.getElementById("chatSidebarExpandBtn");
  if (chatSidebarToggle) chatSidebarToggle.onclick = toggleChatSidebar;
  if (chatSidebarExpandBtn) chatSidebarExpandBtn.onclick = toggleChatSidebar;

  console.log('[chat.js] initChatApp done');
}

// ========== 启动 ==========
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChatApp);
} else {
  initChatApp();
}
c