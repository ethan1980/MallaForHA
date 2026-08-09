const messagesContainer = document.getElementById('messages');
const banner = document.getElementById('newMessagesBanner');

const messageInput = document.getElementById('messageInput');
const channelSelect = document.getElementById('channelSelect');
async function loadChannels() {
  try {
    const response = await fetch('/api/malla/channels');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const channels = await response.json();

    channelSelect.innerHTML = '';

    for (const ch of channels) {
      const option = document.createElement('option');
      option.value = ch;
      option.textContent = ch;
      channelSelect.appendChild(option);
    }

    // Seleccionar el primero disponible
    if (channels.length > 0) {
      channelSelect.value = channels[0];
    }

  } catch (err) {
    console.error('Error cargando canales:', err);
  }
}
const sendButton = document.getElementById('sendButton');

console.log('MALLA APP VERSION 4 - SEND ENABLED');
console.log('Malla cargada', new Date().toLocaleTimeString());

let allMessages = [];
let lastMessageSignature = null;

function channelClass(channel = '') {
  switch (channel.toLowerCase()) {
    case 'longfast':
      return 'longfast';
    case 'sfnarrow':
      return 'sfnarrow';
    case 'mediumslow':
      return 'mediumslow';
    default:
      return '';
  }
}

function renderMessages(messages) {
  messagesContainer.innerHTML = '';

  if (messages.length === 0) {
    messagesContainer.innerHTML =
      '<p style="color:#94a3b8;padding:16px;">No hay mensajes todavía.</p>';
    return;
  }

  for (const m of messages) {
    const author = m.author || m.from || 'Desconocido';
    const text = m.text || m.message || '';
    const time = m.time || '';
    const channel = m.channel || 'Desconocido';

    messagesContainer.innerHTML += `
      <article class="message">
        <div class="message-header">
          <span class="author">${author}</span>
          <span class="time">${time}</span>
        </div>

        <div class="text">${text}</div>

        <div class="meta">
          <span class="channel ${channelClass(channel)}">${channel}</span>

          ${m.rssi != null ? `<span>📶 RSSI ${m.rssi}</span>` : ''}

          ${m.snr != null ? `<span>📡 SNR ${m.snr}</span>` : ''}

          ${m.hops != null ? `<span>↔ Hops ${m.hops}</span>` : ''}
        </div>
      </article>
    `;
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showBanner() {
  banner.classList.remove('hidden');

  clearTimeout(showBanner._timer);

  showBanner._timer = setTimeout(() => {
    banner.classList.add('hidden');
  }, 3000);
}

async function loadMessages() {
  try {
    const response = await fetch('/api/malla/chat');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    let currentSignature = null;

    if (data.length > 0) {
      const last = data[0]; // el backend devuelve primero el más nuevo

      currentSignature =
        (last.from || last.author || '') + '|' +
        (last.time || '') + '|' +
        (last.message || last.text || '');
    }

    if (
      lastMessageSignature !== null &&
      currentSignature !== lastMessageSignature
    ) {
      showBanner();
    }

    lastMessageSignature = currentSignature;

    // Mostrar del más antiguo al más nuevo
    allMessages = [...data].reverse();

    renderMessages(allMessages);

  } catch (err) {
    console.error('Error cargando mensajes:', err);
  }
}

async function sendMessage() {
  const message = messageInput.value.trim();
  const channel = channelSelect.value;

  if (!message) return;

  sendButton.disabled = true;

  try {
    const response = await fetch('/api/malla/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        channel,
      }),
    });

    const result = await response.json();

    if (!response.ok || !result.ok) {
      throw new Error(result.error || 'Error enviando mensaje');
    }

    messageInput.value = '';

    // Actualizar chat tras enviar
    setTimeout(loadMessages, 1000);

  } catch (err) {
    console.error(err);
    alert('No se pudo enviar el mensaje');
  } finally {
    sendButton.disabled = false;
  }
}

// Eventos de envío
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (ev) => {
  if (ev.key === 'Enter') {
    sendMessage();
  }
});

// Carga inicial
loadChannels();
loadMessages();

// Auto-refresh cada 5 segundos
setInterval(loadMessages, 5000);