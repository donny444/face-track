import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI
from pydantic import BaseModel

# โหลด service account key
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

# Access Firestore
db = firestore.client()

# ---------------------------------------------------
# Example: เพิ่มข้อมูลใน students collection
student_ref = db.collection("students").document("65200123")
student_ref.set({
    "first_name": "alex",
    "last_name": "alone",
})

# Example: เพิ่มข้อมูลใน attendances collection
attendance_ref = db.collection("attendances").document()
attendance_ref.set({
    "attendee_id": "3",
    "timestamp": firestore.SERVER_TIMESTAMP
})

print("Data added to Firestore!!")
