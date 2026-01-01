import os
import numpy as np
import tensorflow as tf

from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D, Input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import cv2


VIDEO_DATASET = "dataset/video"
IMG_SIZE = 128


def load_dataset():
    X = []
    y = []

    real_path = os.path.join(VIDEO_DATASET, "real")
    fake_path = os.path.join(VIDEO_DATASET, "fake")

    print("Loading REAL frames...")
    for file in os.listdir(real_path):
        path = os.path.join(real_path, file)
        img = cv2.imread(path)

        if img is None:
            continue

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = img.astype("float32") / 255.0
        X.append(img)
        y.append(0)

    print("Loading FAKE frames...")
    for file in os.listdir(fake_path):
        path = os.path.join(fake_path, file)
        img = cv2.imread(path)

        if img is None:
            continue

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = img.astype("float32") / 255.0
        X.append(img)
        y.append(1)

    X = np.array(X)
    y = np.array(y)

    print("Total samples:", len(X))
    return X, y


print("Loading data...")
X, y = load_dataset()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

classes = np.array([0, 1])

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=y
)

class_weights = {0: class_weights[0], 1: class_weights[1]}

print("\nClass weights:", class_weights)

datagen = ImageDataGenerator(
    rotation_range=5,
    zoom_range=0.1,
    width_shift_range=0.05,
    height_shift_range=0.05,
    horizontal_flip=True
)

datagen.fit(X_train)

base = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights="imagenet"
)

base.trainable = False

x = GlobalAveragePooling2D()(base.output)
x = Dense(128, activation="relu")(x)
x = Dropout(0.3)(x)
output = Dense(1, activation="sigmoid")(x)

model = Model(inputs=base.input, outputs=output)

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

print(model.summary())

history = model.fit(
    datagen.flow(X_train, y_train, batch_size=32),
    validation_data=(X_test, y_test),
    epochs=10,
    class_weight=class_weights
)

model.save("def_video_mobilenet.h5")
print("\nModel saved as def_video_mobilenet.h5")
