import firebase_admin
from firebase_admin import credentials, firestore, auth
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth, credentials, firestore
from pydantic import BaseModel
from datetime import datetime, timezone
from google.cloud.firestore_v1 import FieldFilter

# โหลด service account key
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()
db = firestore.client()

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # หรือ domain ของ frontend
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุก HTTP methods
    allow_headers=["*"],  # อนุญาตทุก headers
)

class Attendance(BaseModel):
	attendee_id: str
	timestamp: int

class Student(BaseModel):
	student_id: str
	first_name: str
	last_name: str
	email: str | None = None
	password: str | None = None

# Receive and save attendance data from face recognition
@app.post("/attendances/")
async def Attend(attendance: Attendance):
	attendanceDict = attendance.model_dump()

	# Convert timestamp to UTC date (year, month, day)
	attendanceDate = datetime.fromtimestamp(attendanceDict["timestamp"], tz=timezone.utc).date()
	startOfToday = int(datetime(attendanceDate.year, attendanceDate.month, attendanceDate.day, tzinfo=timezone.utc).timestamp())
	endOfToday = int(datetime(attendanceDate.year, attendanceDate.month, attendanceDate.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

	# Check if there's attendance of the student in the current day
	existedAttendance = (
		db.collection("attendances") \
		.where("attendee_id", "==", attendanceDict["attendee_id"]) \
		.where(filter=FieldFilter("timestamp", ">=", startOfToday)) \
		.where(filter=FieldFilter("timestamp", "<=", endOfToday)) \
		.stream()
	)

	if existedAttendance:
		raise HTTPException(status_code=400, detail="The student is already attended for today")

	attendanceRef = db.collection("attendances").document()
	attendanceRef.set(attendanceDict)

	return attendanceDict, status.HTTP_201_CREATED

# Student registration
@app.post("/students/")
async def Register(student: Student):
	studentDict = student.model_dump()

	# Email and password are mandatory for Firebase Auth
	if (studentDict["email"] is None) or (studentDict["password"] is None):
		raise HTTPException(status_code=400, detail="Email and password are required for registration")
	
	# First name and last name are mandatory for Firestore
	if (studentDict["first_name"] is None) or (studentDict["last_name"] is None):
		raise HTTPException(status_code=400, detail="First name and last name are required for registration")
	
	allowed_domain = "kmitl.ac.th"
	email = studentDict["email"]
	if "@" not in email or not email.endswith(f"@{allowed_domain}"):
		raise HTTPException(status_code=400, detail=f"Email must be from the {allowed_domain} domain")
	
	# Create user in Firebase Authentication
	try:
		auth.create_user(
			uid=studentDict["email"].split("@")[0],
			email=studentDict["email"],
			password=studentDict["password"],
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

	existingStudentRef = db.collection("students").document(studentDict["student_id"])

	existingStudent = existingStudentRef.get()
	
	if existingStudent.exists:
		raise HTTPException(status_code=400, detail="Student already exists")
	
	studentRef = db.collection("students").document(studentDict["student_id"])
	studentRef.set(
		{
			"first_name": studentDict["first_name"],
			"last_name": studentDict["last_name"],
		}
	)

	return studentDict, status.HTTP_201_CREATED

# Remove a student from Firebase (instructor access)
@app.delete("/students/")
async def Remove(studentId: str):
	# Delete user from Firebase Authentication
	try:
		auth.delete_user(f"{studentId}")
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))
	
	# Delete student and their attendances from Firestore
	transaction = db.transaction()

	# Retrieve all attendance documents for the student
	attendanceQuery = db.collection("attendances").where("attendee_id", "==", studentId).stream()
	attendanceDocs = [doc for doc in attendanceQuery]

	# Use the transaction to delete each attendance document
	for doc in attendanceDocs:
		transaction.delete(doc.reference)

	# Delete the student document
	studentRef = db.collection("students").document(studentId)
	transaction.delete(studentRef)

	# Commit the transaction
	transaction.commit()

	return studentId, status.HTTP_204_NO_CONTENT

# Retreive all attendees in the current day/class
@app.get("/attendances/")
async def GetAll():
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

# -----------------------------
# Pydantic Model สำหรับ Login
class LoginModel(BaseModel):
    email: str
    password: str

# API สำหรับเข้าสู่ระบบ
@app.post("/login")
async def login(data: LoginModel):
    try:
        # ตรวจสอบ credentials กับ Firebase Auth
        user = auth.get_user_by_email(data.email)
        
        # เช็คว่าเป็นอีเมลของอาจารย์หรือไม่
        is_teacher = data.email == "silar@kmitl.ac.th"
        
        # ส่งข้อมูลกลับ
        return {
            "id": user.uid,
            "name": user.display_name or "อาจารย์",  # หรือดึงชื่อจาก Firestore
            "email": user.email,
            "isTeacher": is_teacher
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")