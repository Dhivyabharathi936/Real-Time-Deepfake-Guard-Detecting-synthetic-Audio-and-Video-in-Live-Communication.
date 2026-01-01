import os, sys
import cv2
import numpy as np
import pyttsx3
from tensorflow import keras
from keras.models import load_model

def resource_path(p):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, p)

MODEL_PATH = resource_path("def_video_face_mnv2_compat.h5")
CASCADE_PATH = resource_path("haarcascade_frontalface_default.xml")

print("[INFO] Loading model...")

# 🔥 FIX: allow old MobileNet models
model = load_model(
    MODEL_PATH,
    compile=False,
    custom_objects={"DepthwiseConv2D": keras.layers.DepthwiseConv2D}
)

face_detector = cv2.CascadeClassifier(CASCADE_PATH)
engine = pyttsx3.init()

def preprocess(img):
    img = cv2.resize(img, (128, 128))
    img = img.astype("float32") / 255.0
    return np.expand_dims(img, axis=0)

cap = cv2.VideoCapture(0)
print("🎥 Webcam started — press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        face = frame[y:y+h, x:x+w]
        pred = model.predict(preprocess(face), verbose=0)[0][0]

        label = "FAKE" if pred > 0.5 else "REAL"
        color = (0,0,255) if label == "FAKE" else (0,255,0)

        if label == "FAKE":
            engine.say("Fake detected")
            engine.runAndWait()

        cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
        cv2.putText(frame,f"{label} {pred:.2f}",(x,y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,color,2)

    cv2.imshow("Deepfake Detector", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Webcam closed")
