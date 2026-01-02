Minimal test backend for DeepfakeGuard

This small Flask app provides two endpoints used by the extension for testing:

- WebSocket: `ws://localhost:8000/ws` — send JSON {"frame_id":"...","image_base64":"data:..."} and receive {"frame_id":"...","score":0.123}
- HTTP POST: `http://localhost:8000/predict/frame` — POST JSON {"frame_id":"...","image_base64":"data:..."} and receive JSON {"frame_id":"...","score":0.123}

Requirements
```
pip install -r requirements.txt
```

Run
```
python app.py
```

The server runs on port 8000 by default to match the extension configuration. Scores are randomized for demo purposes.
