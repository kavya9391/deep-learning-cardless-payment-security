import cv2
import face_recognition
import numpy as np
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.models import Model
from cryptography.fernet import Fernet
import secrets
import os
from django.conf import settings

# =====================================
# PATHS & GLOBALS
# =====================================
known_face_dir = os.path.join(settings.MEDIA_ROOT, "known_faces")
os.makedirs(known_face_dir, exist_ok=True)

face_encodings = []
face_names = []

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# =====================================
# SAFE LOAD KNOWN FACES
# =====================================
def load_known_faces():
    global face_encodings, face_names

    face_encodings = []
    face_names = []

    for filename in os.listdir(known_face_dir):
        if not filename.lower().endswith((".jpg", ".png")):
            continue

        image_path = os.path.join(known_face_dir, filename)

        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)

            if not encodings:
                print(f"⚠️ No face found in {filename}, skipping")
                continue

            face_encodings.append(encodings[0])
            face_names.append(os.path.splitext(filename)[0])

        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")

# ❌ DO NOT CALL load_known_faces() HERE
# load_known_faces()

# =====================================
# FACE CAPTURE (SAFE)
# =====================================
def capture_and_store_face(name):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise Exception("Camera not accessible")

    print("📸 Press C to capture | Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Face Capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("c"):
            if len(faces) == 0:
                cap.release()
                cv2.destroyAllWindows()
                raise Exception("No face detected. Try again.")

            x, y, w, h = faces[0]
            face_img = frame[y:y+h, x:x+w]

            img_path = os.path.join(known_face_dir, f"{name}.jpg")
            cv2.imwrite(img_path, face_img)

            cap.release()
            cv2.destroyAllWindows()

            load_known_faces()
            print("✅ Face captured successfully")
            return True

        elif key == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            return False

# =====================================
# RESNET-50 FEATURE EXTRACTION
# =====================================
base_model = ResNet50(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)
model = Model(inputs=base_model.input, outputs=base_model.output)

def extract_features_resnet50(img_path):
    try:
        img = cv2.imread(img_path)
        if img is None:
            return None

        img = cv2.resize(img, (224, 224))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)

        features = model.predict(img)
        return features.flatten()

    except Exception as e:
        print(f"❌ Feature extraction error: {e}")
        return None

# =====================================
# FACE MATCH CHECK (SAFE)
# =====================================
def check_face_match():
    load_known_faces()

    if not face_encodings:
        return "failed"

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "failed"

    encodings = face_recognition.face_encodings(frame)
    if not encodings:
        return "failed"

    matches = face_recognition.compare_faces(face_encodings, encodings[0])
    return "success" if True in matches else "failed"

# =====================================
# OTP & ENCRYPTION
# =====================================
def generate_otp():
    return secrets.token_hex(3).upper()

key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt(data):
    return cipher.encrypt(data.encode()).decode()

def decrypt(data):
    return cipher.decrypt(data.encode()).decode()