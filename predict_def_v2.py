import cv2
import numpy as np
from mtcnn import MTCNN
from keras.models import load_model

MODEL_PATH = "def_video_face_mnv2_compat.h5"
IMG_SIZE = 128

detector = MTCNN()
model = load_model(MODEL_PATH)

def extract_face(frame):
    faces = detector.detect_faces(frame)

    if len(faces) == 0:
        return None
    
    x, y, w, h = faces[0]["box"]
    x, y = max(0, x), max(0, y)
    face = frame[y:y+h, x:x+w]

    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
    face = face.astype("float32") / 255.0
    return face


def predict_video(path):
    cap = cv2.VideoCapture(path)
    frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        face = extract_face(frame)
        if face is not None:
            frames.append(face)

        if len(frames) == 20:
            break

    cap.release()

    if len(frames) == 0:
        print("No face detected in video ❌")
        return

    frames = np.array(frames)

    preds = model.predict(frames)
    score = preds.mean()

    label = "FAKE" if score > 0.5 else "REAL"

    print("\nResult:", label)
    print("Confidence:", round(float(score), 4))


if __name__ == "__main__":
    import sys
    predict_video(sys.argv[1])
