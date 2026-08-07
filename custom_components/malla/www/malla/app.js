const messagesContainer = document.getElementById('messages');
const channelFilter = document.getElementById('channelFilter');
const banner = document.getElementById('newMessagesBanner');

console.log('MALLA APP VERSION 3 - LIVE API MODE');
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
      '<p style="color:#94a3b8">No hay mensajes para este canal.</p>';
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
          <span>📶 RSSI ${m.rssi ?? '—'}</span>
          <span>📡 SNR ${m.snr ?? '—'}</span>
          <span>↔ Hops ${m.hops ?? '—'}</span>
        </div>
      </article>
    `;
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function applyFilter() {
  const selected = channelFilter.value;

  if (selected === 'all') {
    renderMessages(allMessages);
  } else {
    renderMessages(
      allMessages.filter(m => (m.channel || '') === selected)
    );
  }
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
      const last = data[data.length - 1];

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

    applyFilter();

  } catch (err) {
    console.error('Error cargando mensajes:', err);
  }
}

channelFilter.addEventListener('change', applyFilter);

// Carga inicial
loadMessages();

// Auto-refresh cada 5 segundos
setInterval(loadMessages, 5000);