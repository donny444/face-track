import cv2
import face_recognition
import os
import numpy as np
import datetime
import time
import requests

# ---------------- Load Known Faces ----------------
known_face_encodings = []
known_face_names = []

for filename in os.listdir('Faces'):
    if filename.endswith('.jpg') or filename.endswith('.png'):
        img_path = os.path.join('Faces', filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(os.path.splitext(filename)[0])

print(f"Loaded {len(known_face_names)} known faces")            

# ---------------- Camera Setup ----------------
cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Starting camera stream + face recognition... Press 'q' to quit")

# ---------------- Timing Setup ----------------
RECORD_INTERVAL = 120  # 2 ????
last_reset_time = time.time()

# URL ??? server FastAPI
SERVER_URL = "http://127.0.0.1:8000"  # ??????????? IP ??? server ??????????????????

# ???????? last scan ??????????
last_seen = {}

while True:
    ret, frame = cap.read()
    if not ret:
        print("Cannot read frame")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    current_time = time.time()
    detected_names = []

    # ---------------- ???????????? face ----------------
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        # Scale coordinates
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        # ??????????????
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if name != "Unknown":
            detected_names.append(name)

    # ---------------- ?????? last_seen ??? 2 ???? ----------------
    if current_time - last_reset_time >= RECORD_INTERVAL:
        last_seen = {}
        last_reset_time = current_time
        print("Reset last_seen dictionary")

    # ---------------- ???????????? scan ????????????????? ----------------
    timestamp = datetime.datetime.now().isoformat()
    for name in detected_names:
        if name not in last_seen:
            try:
                payload = {
                    "attendee_id": name,
                    "timestamp": timestamp
                }
                response = requests.post(f"{SERVER_URL}/attendance", json=payload)
                print(f"Sent {name}: {response.status_code}, {response.text}")
                last_seen[name] = current_time  # ???????????????????
            except Exception as e:
                print("Error sending to server:", e)

    # ---------------- ???????? ----------------
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, current_time_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow('Face Recognition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
