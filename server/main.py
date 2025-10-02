import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

# โหลด service account key
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # หรือ domain ของ frontend
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุก HTTP methods
    allow_headers=["*"],  # อนุญาตทุก headers
)

# Access Firestore
db = firestore.client()

# -----------------------------
# กำหนด Model สำหรับข้อมูลที่ Pi ส่งมา
class Attendance(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    timestamp: int  # ส่งมาเป็น string ISO format เช่น "2025-09-29T09:15:30"

# -----------------------------
# API endpoint สำหรับบันทึกการเข้าเรียน
@app.post("/attendance")
async def save_attendance(data: Attendance):
    try:
        attendance_ref = db.collection("attendances").document()
        attendance_ref.set({
            "student_id": data.student_id,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "timestamp": data.timestamp  # เก็บเวลาที่ Pi ส่งมา
        })
        return {"message": "บันทึกการเข้าเรียนสำเร็จ"}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# (Optional) Endpoint สำหรับดึงข้อมูลทั้งหมด
@app.get("/attendance")
async def get_attendance():
    docs = db.collection("attendances").stream()
    result = []
    for doc in docs:
        result.append(doc.to_dict())
    return result

# -----------------------------
#Pydantic Model สำหรับข้อมูลนักเรียน
class RegisterModel(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

# API สำหรับลงทะเบียน
@app.post("/register")
async def user(data: RegisterModel):
    try:
        # เช็คว่ามีอีเมลนี้ในระบบแล้วหรือไม่
        user_doc = db.collection("students").document(data.email).get()
        if user_doc.exists:
            raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้งานแล้ว")

        # บันทึกข้อมูลใหม่
        user_ref = db.collection("students").document(data.email)
        user_ref.set({
            "email": data.email,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "password": data.password,  # ในระบบจริง ควรเข้ารหัสก่อนเก็บ
            "created_at": datetime.now().isoformat()
        })
        return {"message": "ลงทะเบียนสำเร็จ"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))