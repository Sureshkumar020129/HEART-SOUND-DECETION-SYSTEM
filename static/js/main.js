/* Main JS — HeartSound AI */
'use strict';

// ---- AOS Init ----
document.addEventListener('DOMContentLoaded', () => {
  if (typeof AOS !== 'undefined') {
    AOS.init({ duration: 600, once: true, easing: 'ease-out-cubic', offset: 60 });
    document.documentElement.classList.add('aos-enabled');
  }

  // Navbar scroll effect
  const nav = document.getElementById('mainNav');
  if (nav) {
    const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Auto-dismiss temporary Django messages after 5s, not persistent risk alerts.
  document.querySelectorAll('.messages-container .alert').forEach(el => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Animate stat numbers (count-up)
  document.querySelectorAll('.stat-number[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    if (isNaN(target)) return;
    let start = 0;
    const duration = 1200;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start = Math.min(start + step, target);
      el.textContent = Math.floor(start);
      if (start >= target) clearInterval(timer);
    }, 16);
  });

  // Theme Toggle Handler
  function initTheme() {
    const saved = localStorage.getItem('hs_theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', saved);
    updateThemeIcons(saved);

    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const current = document.documentElement.getAttribute('data-bs-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', next);
        localStorage.setItem('hs_theme', next);
        updateThemeIcons(next);
      });
    });
  }

  function updateThemeIcons(theme) {
    document.querySelectorAll('.theme-icon').forEach(icon => {
      if (theme === 'light') {
        // Current theme is Light -> Clear SUN icon
        icon.className = 'bi bi-sun-fill theme-icon';
        const parentBtn = icon.closest('.theme-toggle-btn');
        if (parentBtn) {
          parentBtn.setAttribute('title', 'Current Theme: Light Mode (Click to switch to Dark)');
          parentBtn.setAttribute('aria-label', 'Current Theme: Light Mode (Click to switch to Dark)');
        }
      } else {
        // Current theme is Dark -> Clear MOON icon
        icon.className = 'bi bi-moon-stars-fill theme-icon';
        const parentBtn = icon.closest('.theme-toggle-btn');
        if (parentBtn) {
          parentBtn.setAttribute('title', 'Current Theme: Dark Mode (Click to switch to Light)');
          parentBtn.setAttribute('aria-label', 'Current Theme: Dark Mode (Click to switch to Light)');
        }
      }
    });
  }

  initTheme();

  // Upload zone drag & drop
  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('audioFileInput');

  if (uploadZone && fileInput) {
    uploadZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(evt => {
      uploadZone.addEventListener(evt, e => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
      });
    });
    ['dragleave', 'drop'].forEach(evt => {
      uploadZone.addEventListener(evt, e => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
      });
    });
    uploadZone.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length) {
        fileInput.files = files;
        handleFileSelected(files[0]);
      }
    });
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) handleFileSelected(fileInput.files[0]);
    });
  }

  // Browser microphone recording
  initBrowserRecording();
});

// ---- File selected handler ----
function handleFileSelected(file) {
  const uploadZone = document.getElementById('uploadZone');
  const fileNameEl = document.getElementById('selectedFileName');
  const fileSizeEl = document.getElementById('selectedFileSize');
  const audioPreview = document.getElementById('audioPreview');

  if (uploadZone) uploadZone.classList.add('has-file');
  if (fileNameEl) fileNameEl.textContent = file.name;
  if (fileSizeEl) fileSizeEl.textContent = formatBytes(file.size);

  if (audioPreview) {
    const url = URL.createObjectURL(file);
    audioPreview.src = url;
    audioPreview.parentElement.classList.remove('d-none');
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ---- Browser recording ----
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;

function initBrowserRecording() {
  const recordBtn = document.getElementById('recordBtn');
  const stopBtn = document.getElementById('stopBtn');
  const recordStatus = document.getElementById('recordStatus');
  const recordTimer = document.getElementById('recordTimer');
  const recordPreview = document.getElementById('recordPreview');
  const submitRecordBtn = document.getElementById('submitRecordBtn');

  if (!recordBtn) return;

  recordBtn.addEventListener('click', async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        if (recordPreview) { recordPreview.src = url; recordPreview.parentElement.classList.remove('d-none'); }
        if (submitRecordBtn) submitRecordBtn.dataset.blob = url; // Store for submission
        window._recordedBlob = blob;
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorder.start(100);
      recordBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = false;
      if (recordStatus) recordStatus.textContent = 'Recording...';

      recordingSeconds = 0;
      recordingTimer = setInterval(() => {
        recordingSeconds++;
        const m = Math.floor(recordingSeconds / 60).toString().padStart(2,'0');
        const s = (recordingSeconds % 60).toString().padStart(2,'0');
        if (recordTimer) recordTimer.textContent = `${m}:${s}`;
      }, 1000);

    } catch (err) {
      alert('Microphone access denied or not available. Please check your browser permissions.');
    }
  });

  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearInterval(recordingTimer);
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        if (recordStatus) recordStatus.textContent = 'Recording complete. Preview below.';
      }
    });
  }

  if (submitRecordBtn) {
    submitRecordBtn.addEventListener('click', async () => {
      if (!window._recordedBlob) { alert('No recording found.'); return; }
      const formData = new FormData();
      formData.append('audio_data', window._recordedBlob, 'browser_recording.webm');
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
      submitRecordBtn.disabled = true;
      submitRecordBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
      try {
        const resp = await fetch('/analysis/record/', {
          method: 'POST', body: formData,
          headers: { 'X-CSRFToken': csrfToken }
        });
        const data = await resp.json();
        if (data.redirect_url) window.location.href = data.redirect_url;
        else alert('Upload failed: ' + (data.error || 'Unknown error'));
      } catch (e) {
        alert('Network error. Please try again.');
      } finally {
        submitRecordBtn.disabled = false;
        submitRecordBtn.innerHTML = '<i class="bi bi-send me-2"></i>Analyse Recording';
      }
    });
  }
}

// ---- Chatbot ----
function initChatbot() {
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');
  const sendBtn = document.getElementById('sendBtn');
  const clearBtn = document.getElementById('clearChatBtn');

  if (!chatForm) return;

  // Auto-resize textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
  });

  // Send on Enter (Shift+Enter = newline)
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatForm.addEventListener('submit', e => { e.preventDefault(); sendMessage(); });

  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (!confirm('Clear chat history?')) return;
      await fetch('/chatbot/api/clear/', {
        method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      chatMessages.innerHTML = '';
      addSystemMsg('Chat cleared. How can I help you?');
    });
  }

  // Suggested prompts
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      chatInput.value = chip.dataset.prompt || chip.textContent.trim();
      chatInput.focus();
    });
  });

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || sendBtn.disabled) return;

    appendMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    const typingEl = showTyping();

    try {
      const resp = await fetch('/chatbot/api/message/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ message: text }),
      });
      const contentType = resp.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        throw new Error(`The chat service returned an unexpected response (${resp.status}). Please refresh and try again.`);
      }
      const data = await resp.json();
      typingEl.remove();

      if (!resp.ok || data.error) {
        const errorMessage = data.error || `The chat service returned an error (${resp.status}).`;
        appendMessage('assistant', '⚠ ' + errorMessage, 'error');
      } else {
        appendMessage('assistant', data.response, data.source, data.is_emergency, data.is_fallback);
      }
    } catch (err) {
      typingEl.remove();
      const message = err instanceof TypeError
        ? 'Connection error. Please check your connection and try again.'
        : err.message;
      appendMessage('assistant', '⚠ ' + message, 'error');
    } finally {
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  function appendMessage(role, text, source, isEmergency, isFallback) {
    const wrap = document.createElement('div');
    wrap.className = `message-bubble ${role === 'user' ? 'user-msg' : 'assistant-msg'}${isEmergency ? ' emergency-msg' : ''}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble-content';
    // Convert markdown-ish **bold** and newlines
    bubble.innerHTML = formatMessageText(text);
    wrap.appendChild(bubble);

    if (isFallback) {
      const badge = document.createElement('div');
      badge.className = 'fallback-badge';
      badge.innerHTML = '<i class="bi bi-info-circle"></i> Rule-based response';
      wrap.appendChild(badge);
    }

    const time = document.createElement('div');
    time.className = 'message-time text-end';
    time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    wrap.appendChild(time);

    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'message-bubble assistant-msg';
    el.innerHTML = `<div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return el;
  }

  function addSystemMsg(text) {
    const el = document.createElement('div');
    el.className = 'text-center text-muted small py-2';
    el.textContent = text;
    chatMessages.appendChild(el);
  }

  function formatMessageText(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
      .replace(/^• /gm, '&#8226; ');
  }
}

// Init chatbot on its page
document.addEventListener('DOMContentLoaded', initChatbot);

// ---- Cookie helper ----
function getCookie(name) {
  const v = `; ${document.cookie}`;
  const p = v.split(`; ${name}=`);
  if (p.length === 2) return p.pop().split(';').shift();
  return '';
}

// ---- Chart.js helpers ----
function initActivityChart(labels, values) {
  const ctx = document.getElementById('activityChart');
  if (!ctx || typeof Chart === 'undefined') return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Analyses',
        data: values,
        backgroundColor: 'rgba(0, 212, 255, 0.3)',
        borderColor: 'rgba(0, 212, 255, 0.8)',
        borderWidth: 1,
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 1000, easing: 'easeOutQuart' },
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: '#131e35', titleColor: '#00d4ff', bodyColor: '#94a3b8', borderColor: '#1e293b', borderWidth: 1 },
      },
      scales: {
        x: { ticks: { color: '#64748b', maxRotation: 45, font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.03)' } },
        y: { ticks: { color: '#64748b', stepSize: 1, font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
      },
    },
  });
}

function initDonutChart(normal, abnormal) {
  const ctx = document.getElementById('classificationChart');
  if (!ctx || typeof Chart === 'undefined') return;

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Normal', 'Abnormal'],
      datasets: [{
        data: [normal, abnormal],
        backgroundColor: ['rgba(16, 185, 129, 0.7)', 'rgba(239, 68, 68, 0.7)'],
        borderColor: ['rgba(16, 185, 129, 1)', 'rgba(239, 68, 68, 1)'],
        borderWidth: 2,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      animation: { animateScale: true, duration: 1000 },
      plugins: {
        legend: { labels: { color: '#94a3b8', padding: 16, font: { size: 12 } } },
        tooltip: { backgroundColor: '#131e35', titleColor: '#00d4ff', bodyColor: '#94a3b8' },
      },
    },
  });
}

// ---- HeartSound AI Left Sidebar Controller ----
function initSidebar() {
  const sidebar = document.getElementById('appSidebar');
  const toggleBtn = document.getElementById('sidebarToggle');
  const closeBtn = document.getElementById('sidebarCloseBtn');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (!sidebar) return;

  function updateToggleState(isCollapsed) {
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
      toggleBtn.setAttribute('title', isCollapsed ? 'Expand Navigation Sidebar' : 'Collapse Navigation Sidebar');
    }
  }

  function openMobileSidebar() {
    sidebar.classList.add('show');
    if (backdrop) backdrop.classList.add('show');
    document.body.classList.add('sidebar-mobile-open');
    if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
  }

  function closeMobileSidebar() {
    sidebar.classList.remove('show');
    if (backdrop) backdrop.classList.remove('show');
    document.body.classList.remove('sidebar-mobile-open');
    if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
  }

  function expandDesktopSidebar() {
    document.body.classList.remove('sidebar-collapsed');
    localStorage.setItem('hs_sidebar_collapsed', 'false');
    updateToggleState(false);
  }

  function collapseDesktopSidebar() {
    document.body.classList.add('sidebar-collapsed');
    localStorage.setItem('hs_sidebar_collapsed', 'true');
    updateToggleState(true);
  }

  function toggleDesktopSidebar() {
    if (document.body.classList.contains('sidebar-collapsed')) {
      expandDesktopSidebar();
    } else {
      collapseDesktopSidebar();
    }
  }

  // Restore saved collapse state on desktop
  if (window.innerWidth >= 992) {
    const saved = localStorage.getItem('hs_sidebar_collapsed');
    if (saved === 'true') {
      document.body.classList.add('sidebar-collapsed');
      updateToggleState(true);
    } else {
      updateToggleState(false);
    }
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.innerWidth < 992) {
        if (sidebar.classList.contains('show')) {
          closeMobileSidebar();
        } else {
          openMobileSidebar();
        }
      } else {
        toggleDesktopSidebar();
      }
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      closeMobileSidebar();
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', closeMobileSidebar);
  }

  // If a dropdown menu trigger (Analysis, Assessment, Info) is clicked while sidebar is collapsed,
  // automatically expand the sidebar so the user can see and access the sub-options.
  sidebar.querySelectorAll('.sidebar-dropdown-toggle').forEach((dropdownToggle) => {
    dropdownToggle.addEventListener('click', () => {
      if (document.body.classList.contains('sidebar-collapsed')) {
        expandDesktopSidebar();
      }
    });
  });

  // Close slide-out drawer upon clicking navigation links on mobile
  sidebar.querySelectorAll('.sidebar-link:not([data-bs-toggle="collapse"]), .sidebar-sublink').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 992) {
        closeMobileSidebar();
      }
    });
  });

  // Close drawer on Escape key press
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar.classList.contains('show')) {
      closeMobileSidebar();
    }
  });

  // Handle window resize cleanly
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 992 && sidebar.classList.contains('show')) {
      closeMobileSidebar();
    }
  });
}

document.addEventListener('DOMContentLoaded', initSidebar);

