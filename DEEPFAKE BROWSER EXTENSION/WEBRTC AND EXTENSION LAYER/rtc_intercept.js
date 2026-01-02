// rtc_intercept.js
// Injected into page context. Patches RTCPeerConnection to listen for incoming tracks
// and captures frames from the resulting MediaStream to postMessage them to the
// content script for analysis.
(function () {
  if (window.__deepfake_rtc_intercept_installed) return;
  window.__deepfake_rtc_intercept_installed = true;

  function makeHiddenVideoForStream(stream, vidId) {
    const v = document.createElement('video');
    v.autoplay = true;
    v.muted = true;
    v.playsInline = true;
    v.style.position = 'fixed';
    v.style.left = '-9999px';
    v.style.width = '320px';
    v.style.height = '240px';
    v.srcObject = stream;
    document.documentElement.appendChild(v);
    // start playing
    v.play().catch(() => {});
    return v;
  }

  function startCapturingStream(stream, vidId) {
    try {
      const video = makeHiddenVideoForStream(stream, vidId);
      const canvas = document.createElement('canvas');
      canvas.width = 320;
      canvas.height = 240;
      canvas.style.display = 'none';
      document.documentElement.appendChild(canvas);
      const ctx = canvas.getContext('2d');

      const id = setInterval(() => {
        try {
          if (video.readyState < 2) return;
          const w = video.videoWidth || 320;
          const h = video.videoHeight || 240;
          if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w; canvas.height = h;
          }
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
          window.postMessage({ type: 'deepfake_frame', image: dataUrl, vidId: vidId }, '*');
        } catch (e) {}
      }, 1000);

      // store references for potential cleanup
      const meta = { video, canvas, id };
      window.__deepfake_rtc_meta = window.__deepfake_rtc_meta || {};
      window.__deepfake_rtc_meta[vidId] = meta;
      return meta;
    } catch (e) {
      return null;
    }
  }

  function stopCapturingVid(vidId) {
    try {
      const m = window.__deepfake_rtc_meta && window.__deepfake_rtc_meta[vidId];
      if (!m) return;
      clearInterval(m.id);
      try { m.video.remove(); } catch (e) {}
      try { m.canvas.remove(); } catch (e) {}
      delete window.__deepfake_rtc_meta[vidId];
    } catch (e) {}
  }

  // Patch RTCPeerConnection to attach 'track' event listener on creation
  const OriginalPC = window.RTCPeerConnection;
  if (OriginalPC && !OriginalPC.__deepfake_patched) {
    const NewPC = function (...args) {
      const pc = new OriginalPC(...args);
      pc.addEventListener('track', (ev) => {
        try {
          const stream = ev.streams && ev.streams[0] ? ev.streams[0] : null;
          if (!stream) return;
          const vidId = 'pc-' + Date.now() + '-' + Math.floor(Math.random()*10000);
          startCapturingStream(stream, vidId);
        } catch (e) {}
      });
      return pc;
    };
    // copy prototype
    NewPC.prototype = OriginalPC.prototype;
    NewPC.__deepfake_patched = true;
    window.RTCPeerConnection = NewPC;
  }

  // also observe existing RTCPeerConnections (non-standard) via window.getPeerConnections if available
  // no-op otherwise
})();
