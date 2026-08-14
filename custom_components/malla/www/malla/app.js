const messagesContainer = document.getElementById('messages');
const banner = document.getElementById('newMessagesBanner');

const messageInput = document.getElementById('messageInput');
const channelSelect = document.getElementById('channelSelect');

const tabChat = document.getElementById('tabChat');
const tabNodes = document.getElementById('tabNodes');
const tabMap = document.getElementById('tabMap');

const chatView = document.getElementById('chatView');
const nodesView = document.getElementById('nodesView');
const mapView = document.getElementById('mapView');

const nodesList = document.getElementById('nodesList');
const nodesCount = document.getElementById('nodesCount');
const mapCount = document.getElementById('mapCount');

const nodeSearch = document.getElementById('nodeSearch');
const nodeChannelFilter = document.getElementById('nodeChannelFilter');

const sendButton = document.getElementById('sendButton');

const nodeSort = document.getElementById('nodeSort');

console.log('MALLA APP VERSION 7 - MAP FIXED');

let allMessages = [];
let allNodes = [];
let map;
let markerCluster;
let lastMessageSignature = null;

/* -------------------- Canales -------------------- */

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

    if (channels.length > 0) {
      channelSelect.value = channels[0];
    }

  } catch (err) {
    console.error('Error cargando canales:', err);
  }
}

/* -------------------- Utilidades -------------------- */

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

function markerColor(channel = '') {
  switch (String(channel).toLowerCase()) {
    case 'sfnarrow':
      return '#16a34a'; // verde
    case 'longfast':
      return '#2563eb'; // azul
    case 'mediumslow':
      return '#ea580c'; // naranja
    case 'nexus':
      return '#9333ea'; // morado
    case 'iberia':
      return '#dc2626'; // rojo
    case 'madrid':
      return '#0f766e'; // turquesa
    default:
      return '#64748b'; // gris
  }
}

function createColorIcon(color) {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width:18px;
        height:18px;
        border-radius:50%;
        background:${color};
        border:3px solid white;
        box-shadow:0 2px 6px rgba(0,0,0,.45);
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
}

function createClusterIcon(markers) {
  const counts = {};

  markers.getAllChildMarkers().forEach(marker => {
    const channel = marker.options.channel || 'default';
    counts[channel] = (counts[channel] || 0) + 1;
  });

  const dominant = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])[0]?.[0] || 'default';

  const color = markerColor(dominant);
  const count = markers.getChildCount();

  return L.divIcon({
    html: `
      <div style="
        width:42px;
        height:42px;
        border-radius:50%;
        background:${color};
        border:3px solid white;
        display:flex;
        align-items:center;
        justify-content:center;
        color:white;
        font-weight:700;
        font-size:14px;
        box-shadow:0 2px 8px rgba(0,0,0,.35);
      ">${count}</div>
    `,
    className: 'custom-cluster',
    iconSize: [42, 42]
  });
}

/* -------------------- Chat -------------------- */

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
      const last = data[0];

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

    allMessages = [...data].reverse();

    renderMessages(allMessages);

  } catch (err) {
    console.error('Error cargando mensajes:', err);
  }
}

/* -------------------- Nodos -------------------- */

function renderNodes(nodes) {
  nodesCount.textContent = `${nodes.length} nodos`;

  if (nodes.length === 0) {
    nodesList.innerHTML =
      '<p style="color:#94a3b8;padding:16px;">No hay nodos que coincidan con el filtro.</p>';
    return;
  }

  nodesList.innerHTML = nodes.map(node => `
    <div class="node-card">
      <div class="node-header">
        <div class="node-name">${node.name}</div>
        <div class="node-status ${node.online ? 'online' : 'offline'}">
          ${node.online ? '🟢 Online' : '🔴 Offline'}
        </div>
      </div>

      <div class="node-meta">
        <span>📡 ${node.channel || '—'}</span>
        <span>🕒 ${node.last_seen_human || 'desconocido'}</span>
      </div>

      <div class="node-meta" style="margin-top:8px">
        <span class="node-id">ID ${node.id}</span>
      </div>
    </div>
  `).join('');
}

function applyNodeFilters() {
  const search = nodeSearch.value.toLowerCase().trim();
  const channel = nodeChannelFilter.value;
  const sort = nodeSort.value;

  let filtered = allNodes.filter(node => {
    const name = String(node.name || '').toLowerCase();
    const id = String(node.id || '');

    const matchesSearch =
      name.includes(search) || id.includes(search);

    const matchesChannel =
      channel === 'all' || node.channel === channel;

    return matchesSearch && matchesChannel;
  });

  filtered.sort((a, b) => {
    switch (sort) {
      case 'oldest':
        return (a.last_seen || '').localeCompare(b.last_seen || '');

      case 'name':
        return String(a.name || '').localeCompare(
          String(b.name || '')
        );

      case 'recent':
      default:
        return (b.last_seen || '').localeCompare(a.last_seen || '');
    }
  });

  renderNodes(filtered);
}

async function loadNodes() {
  try {
    const response = await fetch('/api/malla/nodes');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    allNodes = await response.json();

    applyNodeFilters();

  } catch (err) {
    console.error('Error cargando nodos:', err);
    nodesList.innerHTML =
      '<p style="color:#ef4444;padding:16px;">Error cargando nodos.</p>';
  }
}

/* -------------------- Navegación -------------------- */

function showChat() {
  chatView.classList.remove('hidden');
  nodesView.classList.add('hidden');
  mapView.classList.add('hidden');

  tabChat.classList.add('active');
  tabNodes.classList.remove('active');
  tabMap.classList.remove('active');
}

function showNodes() {
  chatView.classList.add('hidden');
  nodesView.classList.remove('hidden');
  mapView.classList.add('hidden');

  tabChat.classList.remove('active');
  tabNodes.classList.add('active');
  tabMap.classList.remove('active');

  loadNodes();
}

function showMap() {
  chatView.classList.add('hidden');
  nodesView.classList.add('hidden');
  mapView.classList.remove('hidden');

  tabChat.classList.remove('active');
  tabNodes.classList.remove('active');
  tabMap.classList.add('active');

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      loadMap();

      setTimeout(() => {
        if (map) {
          map.invalidateSize(true);
        }
      }, 300);
    });
  });
}

/* -------------------- Mapa -------------------- */

function initMap() {
  if (map) return;

  map = L.map('map').setView([40.4168, -3.7038], 6);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  markerCluster = L.markerClusterGroup({
    maxClusterRadius: 50,
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
    iconCreateFunction: createClusterIcon
  });

  map.addLayer(markerCluster);
}

async function loadMap() {
  initMap();

  try {
    const response = await fetch('/api/malla/nodes');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const nodes = await response.json();

    const gpsNodes = nodes.filter(
      n => n.lat != null && n.lon != null
    );

    mapCount.textContent = `${gpsNodes.length} nodos con GPS`;

    markerCluster.clearLayers();

const markers = [];

gpsNodes.forEach(node => {
  const marker = L.marker(
    [node.lat, node.lon],
    {
      icon: createColorIcon(markerColor(node.channel)),
      channel: node.channel
    }
  );

  marker.bindPopup(`
    <strong>${node.name}</strong><br>
    📡 ${node.channel || '—'}<br>
    🕒 ${node.last_seen_human || 'desconocido'}<br>
    ${node.online ? '🟢 Online' : '🔴 Offline'}
  `);

  markers.push(marker);
});

markerCluster.addLayers(markers);

    if (gpsNodes.length > 0) {
      const bounds = L.latLngBounds(
        gpsNodes.map(n => [n.lat, n.lon])
      );

      map.fitBounds(bounds, { padding: [40, 40] });
    }

    setTimeout(() => map.invalidateSize(true), 100);

  } catch (err) {
    console.error('Error cargando mapa:', err);
  }
}

/* -------------------- Envío -------------------- */

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

    setTimeout(loadMessages, 1000);

  } catch (err) {
    console.error(err);
    alert('No se pudo enviar el mensaje');
  } finally {
    sendButton.disabled = false;
  }
}

/* -------------------- Eventos -------------------- */

sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (ev) => {
  if (ev.key === 'Enter') {
    sendMessage();
  }
});

tabChat.addEventListener('click', showChat);
tabNodes.addEventListener('click', showNodes);
tabMap.addEventListener('click', showMap);

nodeSearch.addEventListener('input', applyNodeFilters);
nodeChannelFilter.addEventListener('change', applyNodeFilters);
nodeSort.addEventListener('change', applyNodeFilters);

/* -------------------- Inicio -------------------- */

loadChannels();
loadMessages();
showChat();

/* Redibujar mapa al cambiar tamaño */
window.addEventListener('resize', () => {
  if (map && !mapView.classList.contains('hidden')) {
    map.invalidateSize(true);
  }
});

const resizeObserver = new ResizeObserver(() => {
  if (map && !mapView.classList.contains('hidden')) {
    map.invalidateSize(true);
  }
});

resizeObserver.observe(document.body);

/* Auto-refresh */
setInterval(loadMessages, 3000);

setInterval(() => {
  if (!nodesView.classList.contains('hidden')) {
    loadNodes();
  }
}, 20000);