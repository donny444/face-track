import cv2
import face_recognition
import os
import time
from typing import Set

import requests
import numpy as np

API_BASE_URL = os.getenv("SERVER_API_BASE_URL", "http://localhost:8000")
ATTENDANCE_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/attendances/"


def post_attendance(attendee_id: str, sent_attendances: Set[str]) -> None:

    if attendee_id in sent_attendances:
        return

    payload = {
        "attendee_id": attendee_id,
        "timestamp": int(time.time()),
    }

    try:
        response = requests.post(ATTENDANCE_ENDPOINT, json=payload, timeout=5)
        response.raise_for_status()
        sent_attendances.add(attendee_id)
        print(f"Attendance recorded for {attendee_id}")
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 400:
            print(f"Attendance already recorded today for {attendee_id}")
            sent_attendances.add(attendee_id)
        else:
            print(f"HTTP error while posting attendance for {attendee_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Network error while posting attendance for {attendee_id}: {req_err}")

# Load known faces
known_face_encodings = []
known_face_names = []

for filename in os.listdir('faces'):
    if filename.lower().endswith(('.jpg', '.png')):
        img_path = os.path.join('faces', filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(os.path.splitext(filename)[0])

sent_attendances: Set[str] = set()

# Open camera
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Starting camera stream + face recognition... Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Cannot read frame")
        break

    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Find all faces and their encodings in the frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        # Use the first match
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        if name != "Unknown":
            post_attendance(name, sent_attendances)

        # Scale back up
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        # Draw rectangle and label
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow('Face Recognition', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
