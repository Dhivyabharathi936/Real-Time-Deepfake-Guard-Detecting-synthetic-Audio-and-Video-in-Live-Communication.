__The browser extension runs inside meeting tabs (Google Meet, Zoom Web, Teams Web, etc.) and safely observes live WebRTC video after the user has already granted camera/mic access to the site. It:__

<u>Detects live video elements used in calls.</u>

Samples sparse frames (e.g., 1 FPS) from these videos using a hidden canvas.

Sends minimal JPEG frames to the backend for deepfake analysis.

Receives scores and shows non-intrusive warnings in the page.

Provides a clear ON/OFF toggle so users remain in control.

In short, this module is the bridge between the browser’s live call UI and the backend deepfake model, with strong privacy guarantees.

 __2. Owned Files and Responsibilities__
These are the files owned by the Browser Extension & WebRTC module and how they relate to other teams:

__manifest.json__
Defines the extension’s:

Name, description, and version.

Permissions (scripting, storage, activeTab) and backend host permissions.

Background service worker (background.js).

Content script injection (content_script.js).

__Popup UI (popup.html).__

Team impact:

Backend team: Needs correct backend URLs and host permissions.

Security/Privacy: Validates minimal permissions and scope.

__content_script.js__
Injected into meeting pages.

Responsibilities:

Scans for <video> elements used in the call.

Creates a hidden <canvas> per video.

Captures frames at low frequency (e.g., 1 FPS).

Encodes frames as JPEG (dataURL) and sends them to the background.

Receives deepfake scores and displays warning banners in-page.

Reacts to the global enable/disable state stored in extension storage.

__background.js__
Runs as the extension’s background service worker.

Responsibilities:

Opens a WebSocket connection to the backend (for real-time scores).

Falls back to HTTP POST when WebSocket is unavailable.

For each frame:

Receives frame data from content_script.js.

Wraps it in the backend’s expected payload format.

Sends it to /ws or /predict/frame.

For each response:

Maps frame_id back to the corresponding vidId.

Sends the score to the right tab so content_script.js can update banners.

Team impact:

__Backend/API: Must agree on message schema (JSON fields, frame_id, image_base64, timestamp, score structure).__

DevOps: Might configure backend URL, TLS, and deployment environment.

__popup.html__
Provides the extension’s popup UI when clicked in the browser toolbar.

Responsibilities:

Shows a simple toggle: Enable detection / Disable detection.

Reads and updates the detection state in chrome.storage (or equivalent).

Triggers content scripts to start/stop frame capture based on this state.

__ui.css__
Styles the in-page banners that show deepfake risk.

Responsibilities:

Defines color and appearance for:

Safe state.

Warning state.

High-risk (potential deepfake) state.


. How This Module Interacts With Other Modules
With the Backend / API Module
Sends frames and metadata:

image_base64: JPEG-encoded image of the video frame.

timestamp: When the frame was captured.

frame_id: Unique identifier to correlate request and response.

Receives:

A JSON response with at least a score (e.g., score or deepfake_probability) and the same frame_id.

__Protocols:__

__Primary:__ WebSocket (/ws) for streaming frames and scores.

__Fallback:__ HTTP POST (/predict/frame) for request/response.

Contract:
If backend changes the message schema, this module must be updated to match. Conversely, backend can trust this module for frame rate and format.

With the ML / Model Module
The extension is model-agnostic:

It does not care whether the backend uses Xception, CNNs, transformers, or heuristics.

It only expects a score (0–1 or 0–100%) and optional metadata.

Model team:

Defines how the score should be interpreted.

Provides thresholds for “safe / warning / high-risk”.

Extension team:

Applies those thresholds to choose banner color and message.

With the Frontend / Product UI Module
In-page banners are overlaid on top of the active call.

Shared decisions:

Wording: e.g.,

“Safe”

“Warning – Possible manipulation detected”

“High Risk – Potential deepfake detected”

Color and severity mapping.

__Future hooks__:

Could add a “Learn more” link or open a side panel where frontend team controls the content.

With the Security / Privacy / Compliance Module
This module explicitly does not:

Call getUserMedia itself.

Access devices behind user’s back.

Record or store raw video/audio long-term.

Only uses:

Frames derived from already-rendered video elements (after user consent).

In-memory processing and short-lived transmission to backend.

__Collaboration:__

Review permission list and documentation to ensure compliance.

Validate that UX clearly signals when detection is active.




