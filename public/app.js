const state = {
  userId: localStorage.getItem('wa_saas_user_id') || '',
  accounts: [],
  activeAccountId: localStorage.getItem('wa_saas_active_account_id') || '',
  activeChatJid: '',
  messages: [],
  socket: null,
};

const elements = {
  tenantId: document.querySelector('#tenantId'),
  saveTenant: document.querySelector('#saveTenant'),
  accountList: document.querySelector('#accountList'),
  newAccount: document.querySelector('#newAccount'),
  refreshSessions: document.querySelector('#refreshSessions'),
  connectionSummary: document.querySelector('#connectionSummary'),
  qrCard: document.querySelector('#qrCard'),
  qrImage: document.querySelector('#qrImage'),
  chatList: document.querySelector('#chatList'),
  chatSearch: document.querySelector('#chatSearch'),
  activeChatTitle: document.querySelector('#activeChatTitle'),
  activeChatMeta: document.querySelector('#activeChatMeta'),
  activeChatAvatar: document.querySelector('#activeChatAvatar'),
  detailsAvatar: document.querySelector('#detailsAvatar'),
  detailsTitle: document.querySelector('#detailsTitle'),
  detailsSubtitle: document.querySelector('#detailsSubtitle'),
  messagePane: document.querySelector('#messagePane'),
  systemAlerts: document.querySelector('#systemAlerts'),
  composer: document.querySelector('#composer'),
  composerInput: document.querySelector('#composerInput'),
  voiceProfile: document.querySelector('#voiceProfile'),
  voiceFile: document.querySelector('#voiceFile'),
  transformVoice: document.querySelector('#transformVoice'),
  voicePreview: document.querySelector('#voicePreview'),
};

function assertElement(value, name) {
  if (!value) throw new Error(`Missing dashboard element: ${name}`);
  return value;
}

Object.entries(elements).forEach(([name, value]) => assertElement(value, name));
elements.tenantId.value = state.userId;

function api(path, options = {}) {
  if (!state.userId) {
    throw new Error('Set a tenant userId first. Create a User in Prisma Studio and paste its id.');
  }
  return fetch(path, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      'x-user-id': state.userId,
      ...(options.headers || {}),
    },
  }).then(async (response) => {
    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `Request failed with ${response.status}`);
    }
    return response;
  });
}

function getActiveAccount() {
  return state.accounts.find((account) => account.id === state.activeAccountId) || state.accounts[0];
}

function initials(value) {
  return String(value || '?').slice(0, 2).toUpperCase();
}

function formatTime(value) {
  const date = value ? new Date(value) : new Date();
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(date);
}

function extractText(payload) {
  const message = payload?.message || payload?.payload?.message || {};
  return message.conversation
    || message.extendedTextMessage?.text
    || message.imageMessage?.caption
    || message.videoMessage?.caption
    || message.audioMessage && 'Voice message'
    || message.documentMessage?.fileName
    || message.protocolMessage && 'System protocol message'
    || 'Unsupported message payload';
}

function groupChats() {
  const grouped = new Map();
  state.messages.forEach((message) => {
    const jid = message.remoteJid || message.payload?.key?.remoteJid || 'unknown';
    const existing = grouped.get(jid);
    if (!existing || new Date(message.createdAt || 0) > new Date(existing.createdAt || 0)) {
      grouped.set(jid, message);
    }
  });
  return [...grouped.entries()].sort((a, b) => new Date(b[1].createdAt || 0) - new Date(a[1].createdAt || 0));
}

function showAlert(text, tone = 'info') {
  const alert = document.createElement('div');
  alert.className = `alert ${tone === 'danger' ? 'danger' : ''}`;
  alert.textContent = text;
  elements.systemAlerts.prepend(alert);
  setTimeout(() => alert.remove(), 9000);
}

function renderAccounts() {
  elements.accountList.innerHTML = '';
  if (state.accounts.length === 0) {
    elements.accountList.innerHTML = '<div class="account-card"><strong>No accounts yet</strong><small>Create one to receive a QR code.</small></div>';
  }
  state.accounts.forEach((account) => {
    const button = document.createElement('button');
    button.className = `account-card ${account.id === state.activeAccountId ? 'active' : ''}`;
    button.innerHTML = `<strong>${account.label || 'Business WhatsApp'}</strong><small>${account.status || 'DISCONNECTED'} · ${account.phoneNumber || 'No phone linked'}</small>`;
    button.addEventListener('click', () => selectAccount(account.id));
    elements.accountList.append(button);
  });

  const active = getActiveAccount();
  elements.connectionSummary.textContent = active ? `${active.label} · ${active.status}` : 'Create or select an account';
  elements.detailsTitle.textContent = active?.label || 'Business Account';
  elements.detailsSubtitle.textContent = active ? `${active.status} · ${active.phoneNumber || 'Awaiting QR scan'}` : 'No account connected yet';
  elements.detailsAvatar.textContent = initials(active?.label || 'WA');

  if (active?.qrCodeDataUrl) {
    elements.qrImage.src = active.qrCodeDataUrl;
    elements.qrCard.classList.remove('hidden');
  } else {
    elements.qrCard.classList.add('hidden');
  }
}

function renderChats() {
  const query = elements.chatSearch.value.toLowerCase();
  const chats = groupChats().filter(([jid]) => jid.toLowerCase().includes(query));
  elements.chatList.innerHTML = '';
  if (chats.length === 0) {
    elements.chatList.innerHTML = '<div class="chat-row"><strong>No chats yet</strong><small>Incoming Baileys messages will appear here.</small></div>';
    return;
  }
  chats.forEach(([jid, message]) => {
    const row = document.createElement('button');
    row.className = `chat-row ${jid === state.activeChatJid ? 'active' : ''}`;
    const deleted = message.isDeletedBySender ? '<span class="deleted-badge">Deleted by Sender</span>' : '';
    row.innerHTML = `<strong>${jid}</strong><small>${extractText(message.payload || message)}</small>${deleted}`;
    row.addEventListener('click', () => selectChat(jid));
    elements.chatList.append(row);
  });
}

function renderMessages() {
  if (!state.activeChatJid) {
    elements.messagePane.className = 'message-pane empty-state';
    elements.messagePane.innerHTML = '<div><div class="empty-icon">💬</div><h2>Select a chat</h2><p>Choose a conversation from the left panel.</p></div>';
    return;
  }

  const messages = state.messages.filter((message) => (message.remoteJid || message.payload?.key?.remoteJid) === state.activeChatJid);
  elements.messagePane.className = 'message-pane';
  elements.messagePane.innerHTML = '';
  messages.sort((a, b) => new Date(a.createdAt || 0) - new Date(b.createdAt || 0)).forEach((message) => {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${message.fromMe ? 'out' : 'in'}`;
    const deleted = message.isDeletedBySender ? '<span class="deleted-badge">Deleted by Sender</span>' : '';
    bubble.innerHTML = `${deleted}<div>${extractText(message.payload || message)}</div><span class="message-meta">${formatTime(message.createdAt)}</span>`;
    elements.messagePane.append(bubble);
  });
  elements.messagePane.scrollTop = elements.messagePane.scrollHeight;
}

function selectChat(jid) {
  state.activeChatJid = jid;
  elements.activeChatTitle.textContent = jid;
  elements.activeChatMeta.textContent = 'Message retention and live updates enabled';
  elements.activeChatAvatar.textContent = initials(jid);
  elements.composerInput.disabled = false;
  document.querySelector('.send-button').disabled = false;
  renderChats();
  renderMessages();
}

async function selectAccount(accountId) {
  state.activeAccountId = accountId;
  localStorage.setItem('wa_saas_active_account_id', accountId);
  renderAccounts();
  await loadMessages();
}

async function loadSessions() {
  const response = await api('/api/sessions');
  state.accounts = await response.json();
  if (!state.activeAccountId && state.accounts[0]) state.activeAccountId = state.accounts[0].id;
  renderAccounts();
  if (state.activeAccountId) await loadMessages();
}

async function loadMessages() {
  const account = getActiveAccount();
  if (!account) return;
  const response = await api(`/api/accounts/${account.id}/messages?take=200`);
  state.messages = await response.json();
  renderChats();
  renderMessages();
}

function connectSocket() {
  if (!state.userId || typeof window.io !== 'function') return;
  if (state.socket) state.socket.disconnect();
  state.socket = window.io('/', { auth: { userId: state.userId } });
  state.socket.on('tenant.joined', () => showAlert('Live Socket.io tenant room joined.'));
  state.socket.on('wa.qr', (payload) => {
    if (payload.accountId === state.activeAccountId) {
      elements.qrImage.src = payload.qrCodeDataUrl;
      elements.qrCard.classList.remove('hidden');
    }
    showAlert('New QR code generated. Scan it from WhatsApp linked devices.');
  });
  state.socket.on('wa.connected', (payload) => showAlert(`WhatsApp connected: ${payload.phoneNumber || payload.accountId}`));
  state.socket.on('wa.disconnected', () => showAlert('WhatsApp disconnected. Reconnect worker scheduled.', 'danger'));
  state.socket.on('message.upsert', async () => loadMessages());
  state.socket.on('message.deleted_by_sender', (payload) => {
    showAlert(`Deleted by Sender intercepted for message ${payload.waMessageId}`, 'danger');
    loadMessages();
  });
  state.socket.on('call.incoming', (payload) => showAlert(`Incoming ${payload.isVideo ? 'video' : 'voice'} call from ${payload.fromJid}`, 'danger'));
}

elements.saveTenant.addEventListener('click', async () => {
  state.userId = elements.tenantId.value.trim();
  localStorage.setItem('wa_saas_user_id', state.userId);
  connectSocket();
  await loadSessions().catch((error) => showAlert(error.message, 'danger'));
});

elements.refreshSessions.addEventListener('click', () => loadSessions().catch((error) => showAlert(error.message, 'danger')));
elements.chatSearch.addEventListener('input', renderChats);

elements.newAccount.addEventListener('click', async () => {
  const label = window.prompt('Business account label?', 'Business WhatsApp');
  if (!label) return;
  const response = await api('/api/sessions', { method: 'POST', body: JSON.stringify({ label }) });
  const account = await response.json();
  state.activeAccountId = account.id;
  localStorage.setItem('wa_saas_active_account_id', account.id);
  await loadSessions();
});

elements.transformVoice.addEventListener('click', async () => {
  const file = elements.voiceFile.files?.[0];
  if (!file) {
    showAlert('Choose an audio file first.', 'danger');
    return;
  }
  const formData = new FormData();
  formData.append('audio', file);
  const response = await api(`/api/voice/transform?voiceProfile=${elements.voiceProfile.value}`, { method: 'POST', body: formData });
  const blob = await response.blob();
  elements.voicePreview.src = URL.createObjectURL(blob);
  elements.voicePreview.classList.remove('hidden');
  showAlert('Voice profile transformed to OGG/Opus.');
});

elements.composer.addEventListener('submit', (event) => {
  event.preventDefault();
  showAlert('Composer UI is ready; add a send-message endpoint to dispatch typed messages.');
  elements.composerInput.value = '';
});

renderAccounts();
renderChats();
connectSocket();
if (state.userId) loadSessions().catch((error) => showAlert(error.message, 'danger'));
