import os
import cv2
import numpy as np
import random

from sklearn.model_selection import train_test_split
from sklearn.utils import resample

from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


DATASET_DIR = "dataset/video"
IMG_SIZE = 128
MODEL_NAME = "def_video_face_mnv2_compat.h5"

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def extract_face(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=4,
        minSize=(40, 40)
    )

    if len(faces) == 0:
        return None

    x, y, w, h = faces[0]
    face = img[y:y+h, x:x+w]

    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
    face = face.astype("float32") / 255.0

    return face


def load_labelled_faces():
    X, y = [], []

    for label in ["real", "fake"]:
        folder = os.path.join(DATASET_DIR, label)

        if not os.path.exists(folder):
            continue

        files = os.listdir(folder)
        random.shuffle(files)

        print(f"Loading {label.upper()}...")

        for file in files:
            img = cv2.imread(os.path.join(folder, file))

            if img is None:
                continue

            face = extract_face(img)

            if face is None:
                continue

            X.append(face)
            y.append(0 if label == "real" else 1)

        print(f"→ Loaded {len(X)} total samples so far")

    return np.array(X), np.array(y)


print("\n===== LOADING DATA =====")
X, y = load_labelled_faces()

print("Total:", len(X))


# BALANCE
real = np.where(y == 0)[0]
fake = np.where(y == 1)[0]

m = min(len(real), len(fake))

idx = np.concatenate([
    resample(real, replace=False, n_samples=m),
    resample(fake, replace=False, n_samples=m)
])

X, y = X[idx], y[idx]

print("Balanced:", len(X))


X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

datagen = ImageDataGenerator(
    rotation_range=10,
    zoom_range=0.1,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=True
)

datagen.fit(X_train)

base = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_tensor=Input(shape=(IMG_SIZE, IMG_SIZE, 3))
)

base.trainable = False

x = GlobalAveragePooling2D()(base.output)
x = Dense(128, activation="relu")(x)
out = Dense(1, activation="sigmoid")(x)

model = Model(inputs=base.input, outputs=out)

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

callbacks = [
    EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
    ModelCheckpoint(MODEL_NAME, save_best_only=True)
]

print("\n===== TRAINING =====")

model.fit(
    datagen.flow(X_train, y_train, batch_size=32),
    epochs=20,
    validation_data=(X_val, y_val),
    callbacks=callbacks,
    verbose=1
)

print("\nModel saved:", MODEL_NAME)
