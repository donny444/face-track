# ==============================================================================
# FINAL VERSION: Stable Face Recognition Client
# ==============================================================================
import cv2
import face_recognition
import os
import time
import requests
import shutil
from typing import Set, Dict
from urllib.parse import urlparse

# ==============================================================================
# --- CONFIGURATIONS ---
# ==============================================================================
# **สำคัญ:** ตรวจสอบให้แน่ใจว่า IP นี้คือ IP ของ Notebook (Server) ของคุณ
SERVER_API_BASE_URL = os.getenv("SERVER_API_BASE_URL", "http://localhost:8000") 
FACE_DIR = os.getenv("FACE_DIR", "faces")
if not (SERVER_API_BASE_URL and FACE_DIR):
    raise RuntimeWarning("environment variables not found")

STUDENTS_ENDPOINT = f"{SERVER_API_BASE_URL}/students/"
ATTENDANCE_ENDPOINT = f"{SERVER_API_BASE_URL}/attendances/"

# Directory to store face images
os.makedirs(FACE_DIR, exist_ok=True)

# OpenCV Window Name
WINDOW_NAME = "Attendance Check-in System"

# Face Recognition Settings
FRAME_SKIP_RATE = 2  # ประมวลผลทุกๆ 2 เฟรม (ลดการใช้ CPU)
RESIZE_FACTOR = 0.25 # ย่อขนาดภาพเหลือ 25% เพื่อความเร็ว
TOLERANCE = 0.45     # ค่าความแม่นยำ (ยิ่งน้อยยิ่งเข้มงวด)

# UI Feedback Settings
FEEDBACK_DURATION = 3  # แสดง Feedback ค้างไว้ 3 วินาที
COLOR_SUCCESS = (0, 255, 0)  # Green
COLOR_WARNING = (0, 255, 255) # Yellow
COLOR_ERROR = (0, 0, 255)    # Red
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)

# ==============================================================================
# --- HELPER FUNCTIONS ---
# ==============================================================================

def sync_faces_from_server() -> Dict[str, dict]:
    """
    Downloads student images from the server if they don't exist locally
    and returns a cache of student data.
    """
    print("--- 1. Starting face synchronization from server... ---")
    student_cache = {}
    try:
        response = requests.get(STUDENTS_ENDPOINT, timeout=10)
        response.raise_for_status()
        students = response.json()
        print(f"-> Found {len(students)} students on the server.")

        for student in students:
            student_id = student.get("student_id")
            image_url_from_server = student.get("image_url")
            if not (student_id and image_url_from_server):
                continue
            
            parsed_url = urlparse(image_url_from_server)
            image_path = parsed_url.path
            correct_download_url = f"{SERVER_API_BASE_URL}{image_path}"
            local_filename = os.path.basename(image_path)
            local_filepath = os.path.join(FACE_DIR, local_filename)

            student_cache[student_id] = {"first_name": student.get("first_name", "N/A")}

            if not os.path.exists(local_filepath):
                print(f"-> New student found: {student_id}. Downloading image...")
                try:
                    img_response = requests.get(correct_download_url, stream=True, timeout=10)
                    img_response.raise_for_status()
                    with open(local_filepath, 'wb') as f:
                        shutil.copyfileobj(img_response.raw, f)
                    print(f"-> Successfully downloaded {local_filename}")
                except requests.exceptions.RequestException as img_err:
                    print(f"!!! ERROR: Could not download image for {student_id}: {img_err}")
        
        print("--- Synchronization complete. ---")
        return student_cache

    except requests.exceptions.RequestException as e:
        print(f"!!! FATAL ERROR: Could not connect to the server: {e}")
        print("!!! The program will only use existing local faces.")
        return {}


def post_attendance(attendee_id: str, sent_attendances: Set[str]) -> str:
    """ Posts attendance and returns a status string for UI feedback. """
    if attendee_id in sent_attendances:
        return "ALREADY_ATTENDED"
        
    payload = {"attendee_id": attendee_id, "timestamp": int(time.time())}
    try:
        response = requests.post(ATTENDANCE_ENDPOINT, json=payload, timeout=5)
        response.raise_for_status()
        sent_attendances.add(attendee_id)
        print(f"[SUCCESS] Attendance recorded for {attendee_id} at {time.strftime('%H:%M:%S')}")
        return "SUCCESS"
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 400:
            sent_attendances.add(attendee_id)
            print(f"[WARNING] Already recorded today for {attendee_id}")
            return "ALREADY_ATTENDED"
        else:
            print(f"[ERROR] HTTP error: {http_err}")
            return "NETWORK_ERROR"
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] Network error: {req_err}")
        return "NETWORK_ERROR"


def draw_feedback(frame, message, color):
    """ Draws a feedback banner at the bottom of the frame. """
    h, w, _ = frame.shape
    cv2.rectangle(frame, (0, h - 40), (w, h), color, -1)
    text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
    text_x = (w - text_size[0]) // 2
    cv2.putText(frame, message, (text_x, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_BLACK, 2)

# ==============================================================================
# --- MAIN EXECUTION ---
# ==============================================================================

# 1. Sync data and get student info
student_data_cache = sync_faces_from_server()

# 2. Load known faces from local files
print("\n--- 2. Loading known faces into memory... ---")
known_face_encodings, known_face_names = [], []
for student_id in student_data_cache.keys():
    # Find any image file starting with the student_id
    image_file = next((f for f in os.listdir(FACE_DIR) if f.startswith(student_id)), None)
    if image_file:
        img_path = os.path.join(FACE_DIR, image_file)
        try:
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(student_id)
                print(f"  - Loaded face for: {student_id}")
            else:
                print(f"  - WARNING: No face found in {img_path}")
        except Exception as e:
            print(f"  - ERROR: Could not process {img_path}: {e}")
print(f"--- Finished loading {len(known_face_names)} faces. ---\n")

# 3. Initialize camera, attendance set, and UI variables
sent_attendances: Set[str] = set()
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("!!! FATAL ERROR: Cannot open camera")
    exit()

print("--- 3. Starting camera stream. Press 'q' in the video window to quit ---")

frame_count = 0
feedback_message = ""
feedback_color = COLOR_SUCCESS
feedback_timer = 0

# 4. Main Loop
while True:
    ret, frame = cap.read()
    if not ret:
        print("Cannot read frame, retrying...")
        time.sleep(1)
        continue

    frame_count += 1
    
    # Process only on specified frame rate to save CPU
    if frame_count % FRAME_SKIP_RATE == 0:
        small_frame = cv2.resize(frame, (0, 0), fx=RESIZE_FACTOR, fy=RESIZE_FACTOR)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=TOLERANCE)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
            
            # --- Handle feedback ---
            if name != "Unknown":
                result = post_attendance(name, sent_attendances)
                if result == "SUCCESS":
                    first_name = student_data_cache.get(name, {}).get('first_name', name)
                    feedback_message = f"Check-in Success: {first_name}"
                    feedback_color = COLOR_SUCCESS
                    feedback_timer = time.time()
                elif result == "ALREADY_ATTENDED":
                    feedback_message = "Already Checked In Today"
                    feedback_color = COLOR_WARNING
                    feedback_timer = time.time()
            else:
                feedback_message = "Unknown Face Detected"
                feedback_color = COLOR_ERROR
                feedback_timer = time.time()

            # --- Draw on frame ---
            top, right, bottom, left = [int(v / RESIZE_FACTOR) for v in (top, right, bottom, left)]
            cv2.rectangle(frame, (left, top), (right, bottom), COLOR_SUCCESS, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), COLOR_BLACK, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, COLOR_WHITE, 1)

    # Show feedback if timer is active
    if time.time() - feedback_timer < FEEDBACK_DURATION:
        draw_feedback(frame, feedback_message, feedback_color)
    
    # Display the resulting image
    cv2.imshow(WINDOW_NAME, frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. Cleanup
cap.release()
cv2.destroyAllWindows()
print("--- Program terminated. ---")