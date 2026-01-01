import tensorflow as tf
from tensorflow.keras.models import load_model

old = load_model("def_video_face_mnv2.h5")

old.save("def_video_face_mnv2_compat.h5")
