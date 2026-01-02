// Background service worker: receive frames from content script and forward to backend

console.log('[DeepfakeGuard] background worker started');

const HTTP_BACKEND_URL = 'http://localhost:8000/predict/frame';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

let ws = null;
let wsReady = false;
const pendingMap = new Map(); // frame_id -> { vidId, tabId }

// Reconnect/backoff state
let reconnectDelay = 1000; // start 1s
const MAX_DELAY = 30000; // max 30s
let reconnectTimer = null;

function getWsUrl() {
  // Future: read user-configurable URL from storage; for now use default
  return DEFAULT_WS_URL;
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWS();
  }, reconnectDelay);
  console.log('[DeepfakeGuard] scheduling WS reconnect in', reconnectDelay, 'ms');
  reconnectDelay = Math.min(MAX_DELAY, reconnectDelay * 2);
}

function resetBackoff() {
  reconnectDelay = 1000;
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
}

function connectWS() {
  if (ws) return;
  const WS_URL = getWsUrl();
  try {
    console.log('[DeepfakeGuard] connecting WS ->', WS_URL);
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      wsReady = true;
      console.log('[DeepfakeGuard] WS connected');
      resetBackoff();
    };
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        const frameId = msg.frame_id || msg.frameId || null;
        const meta = pendingMap.get(frameId) || {};
        const payload = { type: 'score', data: msg, vidId: meta.vidId };
        if (meta && meta.tabId) {
          try { chrome.tabs.sendMessage(meta.tabId, payload); } catch (e) { console.warn('[DeepfakeGuard] sendMessage to tab failed', e); }
        } else {
          chrome.tabs.query({}, (tabs) => {
            for (const t of tabs) {
              chrome.tabs.sendMessage(t.id, payload);
            }
          });
        }
        if (frameId) pendingMap.delete(frameId);
      } catch (e) {
        console.error('[DeepfakeGuard] ws onmessage parse error', e);
      }
    };
    ws.onclose = (ev) => {
      wsReady = false;
      ws = null;
      console.warn('[DeepfakeGuard] WS closed', ev && ev.code);
      scheduleReconnect();
    };
    ws.onerror = (e) => {
      console.warn('[DeepfakeGuard] WS error', e);
      // close will trigger reconnect
      try { ws && ws.close(); } catch (e) {}
    };
  } catch (e) {
    console.warn('[DeepfakeGuard] failed to connect WS', e);
    ws = null;
    scheduleReconnect();
  }
}

// initial connect
connectWS();

async function postFrameHTTP(imageDataUrl, vidId, frameId) {
  try {
    const payload = { image_base64: imageDataUrl, timestamp: new Date().toISOString() };
    const resp = await fetch(HTTP_BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      console.warn('[DeepfakeGuard] backend returned', resp.status);
      return;
    }
    const json = await resp.json();
    chrome.tabs.query({}, (tabs) => {
      for (const t of tabs) {
        chrome.tabs.sendMessage(t.id, { type: 'score', data: json, vidId });
      }
    });
  } catch (e) {
    console.error('[DeepfakeGuard] error posting frame', e);
  }
}

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg && msg.type === 'frame' && msg.image) {
    const vidId = msg.vidId || null;
    const frameId = msg.frameId || ('f-' + Date.now() + '-' + Math.floor(Math.random()*10000));
    const tabId = sender && sender.tab && sender.tab.id ? sender.tab.id : null;
    // try WebSocket first
    if (wsReady && ws) {
      try {
        pendingMap.set(frameId, { vidId, tabId });
        ws.send(JSON.stringify({ frame_id: frameId, image_base64: msg.image }));
        return;
      } catch (e) {
        console.warn('[DeepfakeGuard] WS send failed, falling back to HTTP', e);
      }
    }
    postFrameHTTP(msg.image, vidId, frameId, tabId);
  }
});

async function postFrameHTTP(imageDataUrl, vidId, frameId, tabId) {
  try {
    const payload = { image_base64: imageDataUrl, timestamp: new Date().toISOString(), frame_id: frameId };
    const resp = await fetch(HTTP_BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      console.warn('[DeepfakeGuard] backend returned', resp.status);
      return;
    }
    const json = await resp.json();
    const message = { type: 'score', data: json, vidId };
    if (tabId) {
      try { chrome.tabs.sendMessage(tabId, message); } catch (e) { console.warn('[DeepfakeGuard] sendMessage to tab failed', e); }
    } else {
      chrome.tabs.query({}, (tabs) => {
        for (const t of tabs) {
          chrome.tabs.sendMessage(t.id, message);
        }
      });
    }
  } catch (e) {
    console.error('[DeepfakeGuard] error posting frame', e);
  }
}
