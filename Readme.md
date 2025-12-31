# DeepfakeGuard Browser Extension

A real-time deepfake detection browser extension that monitors live video calls on platforms like Google Meet, Zoom Web, and Microsoft Teams.

## Overview

DeepfakeGuard runs inside meeting tabs and observes live WebRTC video **only after** the user has already granted camera/mic access to the site.  
It acts as a bridge between the browser’s call UI and the backend deepfake model, with strong privacy guarantees.

## What It Does

- Detects live `<video>` elements used in calls.
- Samples sparse frames (e.g., 1 FPS) using a hidden `<canvas>`.
- Sends minimal JPEG frames to a backend for deepfake analysis.
- Receives scores and shows non-intrusive warnings in the page.
- Provides a clear ON/OFF toggle so users stay in control.

---

## Owned Files & Responsibilities

### `manifest.json`

Defines the extension’s:

- Name, description, and version.
- Permissions:
  - `scripting`
  - `storage`
  - `activeTab`
- Backend `host_permissions`.
- Background service worker (`background.js`).
- Content script injection (`content_script.js`).
- Popup UI (`popup.html`).

**Team impact:**

- **Backend**: Needs correct backend URLs and host permissions.
- **Security/Privacy**: Validates minimal permissions and scope.

---

### `content_script.js`

Injected into meeting pages.

**Responsibilities:**

- Scans for `<video>` elements used in the call.
- Creates a hidden `<canvas>` per video.
- Captures frames at low frequency (e.g., 1 FPS).
- Encodes frames as JPEG (data URL) and sends them to the background.
- Receives deepfake scores and displays in-page warning banners.
- Reacts to the global enable/disable state stored in extension storage.

---

### `background.js`

Runs as the extension’s background service worker.

**Responsibilities:**

- Opens a WebSocket connection to the backend for real-time scores.
- Falls back to HTTP POST when WebSocket is unavailable.
- For each frame:
  - Receives frame data from `content_script.js`.
  - Wraps it in the backend’s expected payload format.
  - Sends it to `/ws` or `/predict/frame`.
- For each response:
  - Maps `frame_id` back to the corresponding `vidId`.
  - Sends the score to the right tab so `content_script.js` can update banners.

**Team impact:**

- **Backend/API**: Must agree on message schema (`frame_id`, `image_base64`, `timestamp`, `score` fields).
- **DevOps**: May configure backend URL, TLS, and deployment environment.

---

### `popup.html`

Provides the extension’s popup UI when clicked in the browser toolbar.

**Responsibilities:**

- Shows a simple toggle: **Enable detection / Disable detection**.
- Reads and updates detection state in `chrome.storage` (or equivalent).
- Triggers content scripts to start/stop frame capture based on this state.

---

### `ui.css`

Styles the in-page banners that show deepfake risk.

**Responsibilities:**

Defines color and appearance for:

- Safe state.
- Warning state.
- High-risk (potential deepfake) state.

---

## Interactions With Other Modules

### Backend / API Module

**Sends frames and metadata:**

- `image_base64`: JPEG-encoded image of the video frame.
- `timestamp`: When the frame was captured.
- `frame_id`: Unique identifier to correlate request and response.

**Receives:**

- A JSON response with at least:
  - `score` (e.g., `score` or `deepfake_probability`)
  - The same `frame_id`.

**Protocols:**

- **Primary**: WebSocket (`/ws`) for streaming frames and scores.
- **Fallback**: HTTP POST (`/predict/frame`) for request/response.

**Contract:**

- If the backend changes the message schema, this module must be updated.
- Backend can trust this module for frame rate and format.

---

### ML / Model Module

The extension is **model-agnostic**:

- Does not care whether the backend uses Xception, CNNs, transformers, or heuristics.
- Only expects:
  - A score (0–1 or 0–100%).
  - Optional metadata.

**Model team:**

- Defines how the score should be interpreted.
- Provides thresholds for “safe / warning / high-risk”.

**Extension team:**

- Applies those thresholds to choose banner color and message.

---

### Frontend / Product UI Module

In-page banners are overlaid on top of the active call.

**Shared decisions:**

- Wording, for example:
  - “Safe”
  - “Warning – Possible manipulation detected”
  - “High Risk – Potential deepfake detected”
- Color and severity mapping.

**Future hooks:**

- Add a “Learn more” link.
- Open a side panel where the frontend team controls the content.

---

### Security / Privacy / Compliance Module

This module explicitly **does not**:

- Call `getUserMedia` itself.
- Access devices behind the user’s back.
- Record or store raw video/audio long-term.

It **only uses**:

- Frames derived from already-rendered video elements (after user consent).
- In-memory processing and short-lived transmission to the backend.

**Collaboration:**

- Review permission list and documentation to ensure compliance.
- Validate that the UX clearly signals when detection is active.
