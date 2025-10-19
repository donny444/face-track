import cv2
import face_recognition
import os
import time
import threading
import requests
from typing import Set
from tkinter import Tk, Label, StringVar

# ----------- Server API Config -----------
API_BASE_URL = os.getenv("SERVER_API_BASE_URL", "http://localhost:8000")
ATTENDANCE_ENDPOINT = f"{API_BASE_URL.rstrip('/')}/attendances/"

# ----------- Attendance Post Function -----------
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
        print(f"? Attendance recorded for {attendee_id}")
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 400:
            print(f"?? Already recorded today for {attendee_id}")
            sent_attendances.add(attendee_id)
        else:
            print(f"? HTTP error: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"? Network error: {req_err}")


# ----------- Load Known Faces -----------
known_face_encodings = []
known_face_names = []
faces_dir = 'Faces'

for filename in os.listdir(faces_dir):
    if filename.lower().endswith(('.jpg', '.png')):
        img_path = os.path.join(faces_dir, filename)
        image = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(os.path.splitext(filename)[0])

print(f"? Loaded {len(known_face_names)} known faces.")

# ----------- Initialize Variables -----------
sent_attendances: Set[str] = set()
RESET_INTERVAL = 24 * 60 * 60
last_reset_time = time.time()

# ----------- Tkinter UI Setup -----------
root = Tk()
root.title("Face Recognition Status")
root.geometry("600x300")

status_text = StringVar()
status_label = Label(root, textvariable=status_text, font=("Arial", 20))
status_label.pack(expand=True)

status_text.set("Wait For Camera Activate   ...")

# ----------- Camera Setup -----------
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    status_text.set("Can't Open Camera")
    print("Cannot open camera")
else:
    status_text.set("Camera Active")


# ----------- Face Recognition Loop -----------
def update_recognition():
    global last_reset_time

    while True:
        ret, frame = cap.read()
        if not ret:
            status_text.set("Unable to read images from camera")
            time.sleep(1)
            continue

        # Resize and convert
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            status_text.set("Waiting for the face....")
        else:
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                if name != "Unknown":
                    post_attendance(name, sent_attendances)
                    status_text.set(f"Success: {name}")
                else:
                    status_text.set("Unknow")

        # Reset attendance daily
        if time.time() - last_reset_time > RESET_INTERVAL:
            sent_attendances.clear()
            last_reset_time = time.time()
            print("?? Attendance reset for new day")

        time.sleep(0.5)  # Update every 0.5 sec

# ----------- Run Recognition in Background Thread -----------
thread = threading.Thread(target=update_recognition, daemon=True)
thread.start()

# ----------- Start UI Loop -----------
root.mainloop()

# ----------- Cleanup -----------
cap.release()
cv2.destroyAllWindows()
