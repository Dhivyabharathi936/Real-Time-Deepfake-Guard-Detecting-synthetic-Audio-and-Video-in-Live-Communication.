(function () {
  // Content script: find visible <video> elements, accept frames from page
  // injections (rtc_intercept.js), and sample frames at 1 FPS.
  console.log('[DeepfakeGuard] content_script loaded');

  const STATE_KEY = 'deepfake_guard_enabled';
  let enabled = false;
  let intervals = new Map();
  // smoothing state per video id
  const scoreWindows = new Map(); // vidId -> array of recent scores
  const consecutiveAbove = new Map();
  const WINDOW_SIZE = 5;
  const THRESHOLD = 0.75;
  const REQUIRED_CONSECUTIVE = 3;
  const banners = new Map();

  function readEnabled(cb) {
    try {
      if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.get([STATE_KEY], (res) => {
          enabled = res[STATE_KEY] === true;
          cb && cb(enabled);
        });
      } else {
        enabled = false;
        cb && cb(enabled);
      }
    } catch (e) {
      enabled = false;
      cb && cb(enabled);
    }
  }

  // inject ui.css and rtc_intercept.js into page context
  function injectPageAssets() {
    try {
      // css
      const href = chrome.runtime.getURL('ui.css');
      if (!document.querySelector('link[data-deepfake-guard]')) {
        const l = document.createElement('link');
        l.rel = 'stylesheet';
        l.href = href;
        l.setAttribute('data-deepfake-guard', '1');
        (document.head || document.documentElement).appendChild(l);
      }
      // script
      const src = chrome.runtime.getURL('rtc_intercept.js');
      if (!document.querySelector('script[data-deepfake-rtc]')) {
        const s = document.createElement('script');
        s.src = src;
        s.async = false;
        s.setAttribute('data-deepfake-rtc', '1');
        (document.head || document.documentElement).appendChild(s);
        s.onload = () => { try { s.remove(); } catch (e) {} };
      }
    } catch (e) {}
  }

  function startCaptureForVideo(video) {
    if (intervals.has(video)) return;
    const canvas = document.createElement('canvas');
    canvas.style.display = 'none';
    document.documentElement.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    // ensure video has an id we can reference
    if (!video.dataset.deepfakeVidId) video.dataset.deepfakeVidId = 'vid-' + Date.now() + '-' + Math.floor(Math.random()*10000);
    const vidId = video.dataset.deepfakeVidId;

    const id = setInterval(() => {
      if (video.paused || video.ended) return;
      try {
        const w = video.videoWidth || video.clientWidth || 640;
        const h = video.videoHeight || video.clientHeight || 480;
        if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
        if (typeof chrome !== 'undefined' && chrome.runtime) {
          chrome.runtime.sendMessage({ type: 'frame', image: dataUrl, vidId: vidId });
        }
      } catch (e) {
        // drawing cross-origin videos may throw; ignore
      }
    }, 1000);

    intervals.set(video, { id, canvas });
  }

  function stopAllCaptures() {
    for (const [video, { id, canvas }] of intervals.entries()) {
      clearInterval(id);
      try { canvas.remove(); } catch (e) {}
      intervals.delete(video);
    }
  }

  function scanAndAttach() {
    readEnabled((isEnabled) => {
      if (!isEnabled) {
        stopAllCaptures();
        return;
      }
      injectPageAssets();
      const videos = Array.from(document.querySelectorAll('video'));
      videos.forEach((v) => {
        try {
          const rect = v.getBoundingClientRect();
          const style = window.getComputedStyle(v);
          if (rect.width < 20 || rect.height < 20) return;
          if (style && (style.visibility === 'hidden' || style.display === 'none')) return;
          startCaptureForVideo(v);
        } catch (e) {
          startCaptureForVideo(v);
        }
      });
    });
  }

  // listen for frames posted from page context (rtc_intercept.js)
  window.addEventListener('message', (ev) => {
    try {
      const m = ev.data || {};
      if (m && m.type === 'deepfake_frame' && m.image) {
        // forward to background
        if (typeof chrome !== 'undefined' && chrome.runtime) {
          chrome.runtime.sendMessage({ type: 'frame', image: m.image, vidId: m.vidId });
        }
      }
    } catch (e) {}
  }, false);

  // MutationObserver to clean up canvases/videos if nodes are removed
  const mo = new MutationObserver((mutations) => {
    for (const mut of mutations) {
      for (const node of Array.from(mut.removedNodes || [])) {
        // remove any attached interval for removed video elements
        if (node.tagName && node.tagName.toLowerCase() === 'video') {
          try {
            if (intervals.has(node)) {
              const { id, canvas } = intervals.get(node);
              clearInterval(id);
              try { canvas.remove(); } catch (e) {}
              intervals.delete(node);
            }
          } catch (e) {}
        }
      }
    }
  });
  try { mo.observe(document.documentElement || document, { childList: true, subtree: true }); } catch (e) {}

  // receive scores from background and apply smoothing + UI
  if (typeof chrome !== 'undefined' && chrome.runtime) {
    chrome.runtime.onMessage.addListener((msg, sender) => {
      if (!msg || msg.type !== 'score') return;
      const vidId = msg.vidId || (msg.data && msg.data.vidId) || null;
      const score = msg.data && msg.data.score != null ? Number(msg.data.score) : null;
      if (score == null) return;

      const w = scoreWindows.get(vidId) || [];
      w.push(score);
      if (w.length > WINDOW_SIZE) w.shift();
      scoreWindows.set(vidId, w);

      const avg = w.reduce((a,b)=>a+b,0)/w.length;
      const consec = consecutiveAbove.get(vidId) || 0;
      if (avg >= THRESHOLD) {
        const nowc = consec + 1;
        consecutiveAbove.set(vidId, nowc);
        if (nowc >= REQUIRED_CONSECUTIVE) showBanner(vidId, avg, 'danger');
      } else if (avg >= 0.4) {
        consecutiveAbove.set(vidId, 0);
        showBanner(vidId, avg, 'warning');
      } else {
        consecutiveAbove.set(vidId, 0);
        hideBanner(vidId);
      }
    });
  }

  function showBanner(vidId, score, level) {
    let b = banners.get(vidId);
    if (!b) {
      b = document.createElement('div');
      b.className = 'deepfake-guard-banner deepfake-guard-' + (level === 'danger' ? 'danger' : level === 'warning' ? 'warning' : 'safe');
      b.style.display = 'block';
      b.style.position = 'fixed';
      b.style.top = '8px';
      b.style.right = '8px';
      b.style.zIndex = 2147483647;
      b.style.padding = '8px 12px';
      b.style.borderRadius = '6px';
      document.documentElement.appendChild(b);
      banners.set(vidId, b);
    }
    b.textContent = (level === 'danger' ? '\u26A0\uFE0F Potential Deepfake Detected — ' : level === 'warning' ? '\u26A0 Warning — ' : 'Safe — ') + 'Confidence: ' + Math.round(score*100) + '%';
    b.className = 'deepfake-guard-banner deepfake-guard-' + (level === 'danger' ? 'danger' : level === 'warning' ? 'warning' : 'safe');
  }

  function hideBanner(vidId) {
    const b = banners.get(vidId);
    if (b) {
      try { b.remove(); } catch (e) {}
      banners.delete(vidId);
    }
  }

  // react to storage changes (toggle ON/OFF)
  if (typeof chrome !== 'undefined' && chrome.storage) {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local' && changes[STATE_KEY]) {
        enabled = changes[STATE_KEY].newValue === true;
        if (enabled) scanAndAttach(); else stopAllCaptures();
      }
    });
  }

  // initial scan and periodic re-scan
  scanAndAttach();
  setInterval(scanAndAttach, 5000);
})();
