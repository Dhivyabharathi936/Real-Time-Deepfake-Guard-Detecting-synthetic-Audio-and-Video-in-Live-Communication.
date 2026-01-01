import cv2
import sys
import numpy as np
from mtcnn import MTCNN
from keras.models import load_model
from keras.preprocessing.image import img_to_array

MODEL_PATH = "def_video_face_mnv2_compat.h5"

if len(sys.argv) < 2:
    print("Usage: python predict_video_overlay.py <video_path>")
    sys.exit()

VIDEO_PATH = sys.argv[1]

print("\nLoading model...")
model = load_model(MODEL_PATH)

detector = MTCNN()

cap = cv2.VideoCapture(VIDEO_PATH)

# Output video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = None

print("\nProcessing video... Press Q to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = detector.detect_faces(rgb)

    for face in faces:
        x, y, w, h = face["box"]

        # safety bounds
        x = max(0, x)
        y = max(0, y)

        face_img = rgb[y:y+h, x:x+w]

        try:
            face_img = cv2.resize(face_img, (128, 128))
        except:
            continue

        face_img = face_img.astype("float") / 255.0
        face_img = img_to_array(face_img)
        face_img = np.expand_dims(face_img, axis=0)

        prediction = model.predict(face_img, verbose=0)[0][0]

        label = "FAKE" if prediction >= 0.5 else "REAL"
        conf = prediction if prediction >= 0.5 else 1 - prediction

        color = (0, 0, 255) if label == "FAKE" else (0, 255, 0)

        # draw box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # draw label
        text = f"{label} ({conf:.2f})"
        cv2.putText(
            frame,
            text,
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    # initialize writer once we know frame size
    if out is None:
        h, w = frame.shape[:2]
        out = cv2.VideoWriter("output_overlay.mp4", fourcc, 20, (w, h))

    out.write(frame)

    cv2.imshow("Deepfake Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("\nSaved: output_overlay.mp4\n")
