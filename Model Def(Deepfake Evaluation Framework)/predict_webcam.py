import cv2
import numpy as np
from keras.models import load_model
from mtcnn import MTCNN

MODEL_PATH = "def_video_face_mnv2_compat.h5"
IMG_SIZE = 128

print("Loading model...")
model = load_model(MODEL_PATH)
detector = MTCNN()

def preprocess_face(face):
    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
    face = face.astype("float32") / 255.0
    face = np.expand_dims(face, axis=0)
    return face


cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Webcam not detected")
    exit()

print("🎥 Webcam started — Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)

    for f in faces:
        x, y, w, h = f["box"]

        x, y = max(0, x), max(0, y)
        face = rgb[y:y+h, x:x+w]

        if face.size == 0:
            continue

        processed = preprocess_face(face)
        pred = model.predict(processed, verbose=0)[0][0]

        label = "FAKE" if pred > 0.5 else "REAL"
        conf = pred if pred > 0.5 else 1 - pred

        color = (0, 0, 255) if label == "FAKE" else (0, 255, 0)

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(
            frame,
            f"{label} ({conf:.2f})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    cv2.imshow("Deepfake Detector - Webcam", frame)

    # ===== Quit key =====
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
print("Webcam closed.")
