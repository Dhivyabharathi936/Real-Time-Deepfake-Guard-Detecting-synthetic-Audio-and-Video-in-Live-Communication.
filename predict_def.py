import cv2
import numpy as np
import sys
from tensorflow.keras.models import load_model

MODEL_PATH = "def_video_only.h5"
IMG_SIZE = 128

model = load_model(MODEL_PATH)


def load_video_frames(video_path, max_frames=20):
    cap = cv2.VideoCapture(video_path)

    frames = []
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        frame = frame.astype("float32") / 255.0
        frames.append(frame)

        count += 1
        if count >= max_frames:
            break

    cap.release()

    frames = np.array(frames)

    return frames


def predict(video_path):
    frames = load_video_frames(video_path)

    # 🔎 DEBUG — SEE HOW MANY FRAMES WE GOT
    print("Loaded frames:", frames.shape)

    if frames.shape[0] == 0:
        raise ValueError("No frames read — the video cannot be decoded.")

    preds = model.predict(frames)

    avg_pred = np.mean(preds)

    label = "FAKE" if avg_pred > 0.5 else "REAL"

    print(f"\nResult: {label}")
    print(f"Confidence: {float(avg_pred):.4f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predict_def.py <video_file>")
        sys.exit()

    predict(sys.argv[1])
