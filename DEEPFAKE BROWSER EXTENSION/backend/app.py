from flask import Flask, request, jsonify
from flask_sock import Sock
import json
import random

app = Flask(__name__)
sock = Sock(app)


@sock.route('/ws')
def websocket(ws):
    """Simple echo-like websocket: accepts JSON with optional `frame_id` and replies with a fake score."""
    while True:
        data = ws.receive()
        if data is None:
            break
        try:
            msg = json.loads(data)
        except Exception:
            msg = {}
        frame_id = msg.get('frame_id')
        score = round(random.random(), 4)
        resp = {'frame_id': frame_id, 'score': score}
        ws.send(json.dumps(resp))


@app.route('/predict/frame', methods=['POST'])
def predict_frame():
    """HTTP fallback endpoint: accepts JSON with `image_base64` and optional `frame_id`, returns a fake score."""
    data = request.get_json(force=True, silent=True) or {}
    frame_id = data.get('frame_id')
    score = round(random.random(), 4)
    return jsonify({'frame_id': frame_id, 'score': score})


if __name__ == '__main__':
    # Run in debug mode on port 8000 to match extension defaults
    app.run(host='0.0.0.0', port=8000, debug=True)
