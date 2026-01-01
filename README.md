Awesome — here’s a clean **README.md** you can paste into your project 👇

(You can edit the project name and author as you like.)

---

# 🛡️ Real-Time Deepfake Detector (Webcam)

Detect deepfake faces from a live webcam feed using a CNN model and OpenCV — with voice alerts when fake is detected.

This project loads a pre-trained deepfake classification model (`.h5`) and performs real-time inference on detected faces.

---

## ✨ Features

* 🎥 Real-time webcam detection
* 🤖 CNN–based deepfake classifier
* 👤 Face detection using Haar Cascade
* 🔊 Voice alert: *“Fake detected!”*
* 🖥️ Works on CPU (GPU optional)
* 📦 Build as EXE (runs without Python)

---

## 📁 Project Structure

```
deepfake-detector/
│
├── predict_webcam_v2.py
├── def_video_face_mnv2_compat.h5
├── haarcascade_frontalface_default.xml
├── README.md
└── (optional) models/
```

> Make sure the `.h5` and `.xml` files are in the **same folder** as the script.

---

## ⚙️ Requirements

* Windows 10+
* Python **3.11**
* Webcam

### Install dependencies

Create (recommended) virtual environment:

```bash
python -m venv tfenv
tfenv\Scripts\activate
```

Install packages:

```bash
pip install tensorflow==2.15.0 tensorflow-intel==2.15.0 keras==2.15.0
pip install opencv-python numpy pyttsx3
```

---

## ▶️ Run the app

```bash
python predict_webcam_v2.py
```

### Controls

| Key | Action       |
| --- | ------------ |
| Q   | Quit program |

---

## 🧠 Model Details

* Input size: **128 × 128**
* Output: probability (0–1)

  * `REAL` if prediction ≤ 0.5
  * `FAKE` if prediction > 0.5

---

## 🖥 Build EXE (No Python Needed)

From the project folder:

```bash
pyinstaller --onefile --noconsole ^
 --hidden-import pyttsx3 ^
 --add-data "def_video_face_mnv2_compat.h5;." ^
 --add-data "haarcascade_frontalface_default.xml;." ^
 predict_webcam_v2.py
```

Your EXE will appear here:

```
dist/predict_webcam_v2.exe
```

---

## ⚡ (Optional) Enable GPU

Your laptop has **RTX 3050** ✔

GPU support requires:

* NVIDIA driver installed
* TensorFlow GPU build matching CUDA version

Check GPU:

```bash
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

If it prints:

```
[]
```

then TensorFlow is still using CPU.
(We can configure GPU later if needed.)

---

## 🛠 Troubleshooting

### ❌ Model not found

```
OSError: No file or directory found
```

Make sure:

```
predict_webcam_v2.py
def_video_face_mnv2_compat.h5
haarcascade_frontalface_default.xml
```

are in the same folder.

---

### ❌ Face detector error

```
!empty() in function 'CascadeClassifier'
```

Your XML file is missing or not included inside EXE.

Add this when building:

```
--add-data "haarcascade_frontalface_default.xml;."
```

---

### ❌ “DepthwiseConv2D groups” error

You are using incompatible Keras.

Fix:

```bash
pip install keras==2.15.0
```

---

## 📜 License

Educational / research use only.
Do **not** use for surveillance or privacy-violating purposes.

---

## 👤 Author

Monish

