import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import jwt
from fastapi import FastAPI, HTTPException, status, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1 import FieldFilter
from pydantic import BaseModel
from auth_middleware import AuthMiddleware, JWT_SECRET_KEY, JWT_ALGORITHM, EXEMPT_ROUTES
from typing import Optional
import shutil


# โหลด service account key
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()
db = firestore.client()

app.add_middleware(
	AuthMiddleware,
	exempt_paths=EXEMPT_ROUTES
)

load_dotenv(".env.local")
TOKEN_TTL_MINUTES = int(os.getenv("JWT_TOKEN_TTL_MINUTES", "60"))
VALID_EMAIL_DOMAIN = os.getenv("VALID_EMAIL_DOMAIN", "@kmitl.ac.th")
if not (TOKEN_TTL_MINUTES and VALID_EMAIL_DOMAIN):
    raise RuntimeWarning("environment variables not found")

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
	timestamp: int | None = 0

class Attendee(Attendance):
	first_name: str | None = "Unknown"
	last_name: str | None = "Unknown"

class Student(BaseModel):
	email: str
	student_id: str | None = None
	first_name: str | None = None
	last_name: str | None = None
	password: str | None = None

class Instructor(BaseModel):
	email: str
	first_name: str | None = None
	last_name: str | None = None
	password: str | None = None

# Receive and save attendance data from face recognition
@app.post("/attendances/", status_code=status.HTTP_201_CREATED)
async def Attend(attendance: Attendance):
	attendeeId = attendance.attendee_id
	if not attendeeId:
		raise HTTPException(status_code=400, detail="attendeeId is required in the request body")

	timestamp = int(datetime.now(tz=timezone.utc).timestamp())

	# Convert timestamp to UTC date (year, month, day)
	attendanceDate = datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
	startOfToday = int(datetime(attendanceDate.year, attendanceDate.month, attendanceDate.day, tzinfo=timezone.utc).timestamp())
	endOfToday = int(datetime(attendanceDate.year, attendanceDate.month, attendanceDate.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

	# Check if there's attendance of the student in the current day
	existedAttendance = (
		db.collection("attendances") \
		.where(filter=FieldFilter("attendee_id", "==", attendeeId)) \
		.where(filter=FieldFilter("timestamp", ">=", startOfToday)) \
		.where(filter=FieldFilter("timestamp", "<=", endOfToday)) \
		.stream()
	)

	if existedAttendance:
		raise HTTPException(status_code=400, detail="The student is already attended for today")

	# attendanceDict = {
	# 	"attendee_id": attendeeId,
	# 	"timestamp": timestamp,
	# }
	# attendanceData = Attendance(
	# 	attendee_id=attendeeId,
	# 	timestamp=timestamp
	# )
	attendance.timestamp = timestamp
	attendanceDict = attendance.model_dump()

	attendanceRef = db.collection("attendances").document()
	attendanceRef.set(attendanceDict)

	return {
		"message": "Attendance recorded successfully",
		"data": attendanceDict
	}

# Student registration
@app.post("/students/", status_code=status.HTTP_201_CREATED)
async def Register(student: Student):
	studentDict = student.model_dump()

	# Email and password are mandatory for Firebase Auth
	if (studentDict["email"] is None) or (studentDict["password"] is None):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required for registration")
	
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
	
	studentName = {
		"first_name": studentDict["first_name"],
		"last_name": studentDict["last_name"],
	}
	
	studentRef = db.collection("students").document(studentDict["student_id"])
	studentRef.set(studentName)

	return { "message": "Student registered successfully" }

# Login (for instructor)
@app.post("/login/", status_code=status.HTTP_200_OK)
async def Login(instructor: Instructor):
	instructorDict = instructor.model_dump()

	if (instructorDict["email"] is None) or (instructorDict["password"] is None):
		raise HTTPException(status_code=400, detail="Email and password are required for login")

	try:
		auth.get_user_by_email(instructorDict["email"])
	except auth.UserNotFoundError:
		raise HTTPException(status_code=404, detail="User not found")
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

	instructorDocs = list(
		db.collection("instructors")
		.where("email", "==", instructorDict["email"])
		.limit(1)
		.stream()
	)
	if not instructorDocs:
		raise HTTPException(status_code=404, detail="Instructor not found")

	instructorDoc = instructorDocs[0]
	tokenPayload = {
		"sub": instructorDoc.id,
		"email": instructorDict["email"],
		"iat": int(datetime.now(tz=timezone.utc).timestamp()),
		"exp": int((datetime.now(tz=timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
	}

	token = jwt.encode(tokenPayload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
	instructorDict = instructorDoc.to_dict()

	return {
		"message": "Login successful",
		"data": instructorDict,
		"token": token
	}

# Remove a student from Firebase (instructor access)
@app.delete("/students/", status_code=status.HTTP_200_OK)
async def Remove(student: Student):
	studentDict = student.model_dump()
	studentId = studentDict["student_id"]

	if not studentId:
		raise HTTPException(status_code=400, detail="ID of a student is required for removal")

	# Delete user from Firebase Authentication
	try:
		uid = auth.get_user_by_email(f"{studentId}" + VALID_EMAIL_DOMAIN).uid
		# print("Deleting user with UID:", uid)
		auth.delete_user(uid)
	except auth.UserNotFoundError:
		raise HTTPException(status_code=404, detail="User not found")
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))
	
	# Delete student and their attendances from Firestore
	transaction = db.transaction()

	# Retrieve all attendance documents for the student
	attendanceQuery = db.collection("attendances").where("student_id", "==", studentId).stream()
	attendanceDocs = [doc for doc in attendanceQuery]

	# Use the transaction to delete each attendance document
	for doc in attendanceDocs:
		transaction.delete(doc.reference)

	# Delete the student document
	studentRef = db.collection("students").document(studentId)
	transaction.delete(studentRef)

	# Commit the transaction
	transaction.commit()

	return { "message": "Student and their attendances deleted successfully" }

# Retrieve attendees in the current day/class sorted descendingly by timestamp
@app.get("/attendances/", status_code=status.HTTP_200_OK)
async def GetAttendances(recent: bool = Query(False)):
	now = datetime.now(timezone.utc)
	startOfToday = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp())
	endOfToday = int(datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())
	docs = (db.collection("attendances") \
		.where(filter=FieldFilter("timestamp", ">=", startOfToday)) \
		.where(filter=FieldFilter("timestamp", "<=", endOfToday)) \
		.order_by("timestamp", direction=firestore.Query.DESCENDING) \
	)
	if recent:
		docs = docs.limit(5)
	docs = docs.stream()


	result = []
	for doc in docs:
		attendance = doc.to_dict()

		if type(attendance["timestamp"]) is not int:
			attendance["timestamp"] = 0
		
		if "attendee_id" not in attendance:
			attendance["first_name"] = "Unknown"
			attendance["last_name"] = "Unknown"
			attendance["attendee_id"] = "Unknown"
		else:
			studentRef = db.collection("students").document(attendance["attendee_id"])
			studentDoc = studentRef.get()
			if studentDoc.exists:
				student = studentDoc.to_dict()
				attendance["first_name"] = student["first_name"]
				attendance["last_name"] = student["last_name"]
			else:
				attendance["first_name"] = "Unknown"
				attendance["last_name"] = "Unknown"

		doc = Attendee(**attendance)
		docDict = doc.model_dump()
		result.append(docDict)
	
	return {
		"message": "Today's attendances retrieved successfully",
		"data": result
	}

# Retrieve list of all students registered in the class
@app.get("/students/", status_code=status.HTTP_200_OK)
async def GetStudents(head: bool = Query(True), search: str = Query(None)):
	now = datetime.now(timezone.utc)
	startOfToday = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp())
	endOfToday = int(datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

	students = (db.collection("students"))
	if head:
		students = students.limit(5)
	students = students.stream()

	result = []
	for student in students:
		studentDict = student.to_dict()
		studentDict["attendee_id"] = str(student.id)

		attendances = list(db.collection("attendances") \
			.where(filter=FieldFilter("attendee_id", "==", str(student.id))) \
			.where(filter=FieldFilter("timestamp", ">=", startOfToday)) \
			.where(filter=FieldFilter("timestamp", "<=", endOfToday)) \
			.limit(1) \
			.stream()
		)
		attendance = attendances[0] if attendances else None

		if attendance is not None:
			attendanceDict = attendance.to_dict()
			studentDict["timestamp"] = attendanceDict["timestamp"]
		else:
			studentDict["timestamp"] = 0

		student = Attendee(**studentDict)
		studentDict = student.model_dump()
		result.append(studentDict)

	if search:
		pass
			# docs = (
			# 	db.collection("students")
			# 	.where(filter=FieldFilter("first_name", ">=", search))
			# 	.where(filter=FieldFilter("first_name", "<=", search + "\uf8ff"))
			# 	.order_by("first_name", direction=firestore.Query.ASCENDING)
			# 	.limit(5)
			# )
			# # Also search by last_name
			# last_name_docs = (
			# 	db.collection("students")
			# 	.where(filter=FieldFilter("last_name", ">=", search))
			# 	.where(filter=FieldFilter("last_name", "<=", search + "\uf8ff"))
			# 	.order_by("last_name", direction=firestore.Query.ASCENDING)
			# 	.limit(5)
			# )
			# # Merge results, avoiding duplicates
			# doc_ids = set()
			# result_docs = []
			# for doc in docs.stream():
			# 	doc_ids.add(doc.id)
			# 	result_docs.append(doc)
			# for doc in last_name_docs.stream():
			# 	if doc.id not in doc_ids:
			# 		result_docs.append(doc)
			# docs = result_docs

	return {
		"message": "Student list and their attending time retrieved successfully",
		"data": result
	}

# -----------------------------
#Pydantic Model สำหรับข้อมูลนักเรียน
class RegisterModel(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str



# --- 1. แก้ไขและตั้งค่า Static Files ให้ถูกต้อง ---
# สร้างโฟลเดอร์ชื่อ 'public_uploads' ในโปรเจกต์ของคุณ
# ถ้ามี request มาที่ URL /uploaded_images/... ให้ไปหาไฟล์ในโฟลเดอร์ public_uploads
app.mount("/uploaded_images", StaticFiles(directory="Faces"), name="static")

# API สำหรับลงทะเบียน (ฉบับแก้ไขเพื่อบันทึกไฟล์ลงเครื่อง)
@app.post("/register")
async def register(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    print(f"Received registration request for email: {email}")

    allowed_domain = "kmitl.ac.th"
    if not email.endswith(f"@{allowed_domain}"):
        raise HTTPException(status_code=400, detail=f"ต้องใช้อีเมลของ {allowed_domain} เท่านั้น")
        
    student_id = email.split('@')[0]
    image_url_to_save = None # ตัวแปรสำหรับเก็บ URL ที่จะบันทึกลง DB

    student_doc_ref = db.collection("students").document(student_id)
    if student_doc_ref.get().exists:
        raise HTTPException(status_code=400, detail="รหัสนักศึกษานี้มีอยู่ในระบบแล้ว")
    
    # --- vvv 2. แก้ไขส่วนจัดการรูปภาพทั้งหมด vvv ---
    if image:
        if not image.content_type in ["image/jpeg", "image/jpg", "image/png"]:
            raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ .jpg และ .png เท่านั้น")
        
        try:
            # กำหนดโฟลเดอร์ที่จะเก็บไฟล์
            UPLOAD_DIR = "Faces"
            os.makedirs(UPLOAD_DIR, exist_ok=True) # สร้างโฟลเดอร์ถ้ายังไม่มี

            # สร้างชื่อไฟล์ใหม่ที่ไม่ซ้ำกัน
            file_extension = image.filename.split('.')[-1]
            unique_filename = f"{student_id}.{file_extension}"
            file_location = os.path.join(UPLOAD_DIR, unique_filename)
            
            # บันทึกไฟล์ลงในโฟลเดอร์ที่กำหนด
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(image.file, file_object)
            
            # สร้าง URL ที่ถูกต้องสำหรับเข้าถึงไฟล์นี้
            image_url_to_save = f"http://localhost:8000/Faces/{unique_filename}"
            print(f"File saved locally at: {file_location}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการบันทึกรูปภาพ: {str(e)}")
    # --- ^^^ สิ้นสุดส่วนแก้ไข ^^^ ---

    try:
        # สร้างผู้ใช้ใน Firebase Authentication
        user_record = auth.create_user(
            uid=student_id,
            email=email,
            password=password,
            display_name=f"{first_name} {last_name}",
            photo_url=image_url_to_save # ใช้ URL ที่สร้างขึ้นใหม่
        )

        # บันทึกข้อมูลลง Firestore
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "image_url": image_url_to_save # ใช้ URL ที่สร้างขึ้นใหม่
        }
        db.collection("students").document(student_id).set(user_data)

        return {"message": "ลงทะเบียนสำเร็จ", "uid": user_record.uid, "image_url": image_url_to_save}

    except Exception as e:
        # ส่วนจัดการ Error (เหมือนเดิม)
        try:
            if auth.get_user(student_id):
                auth.delete_user(student_id)
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}")



# -----------------------------
# Pydantic Model สำหรับ Login (กลับมาใช้แบบเดิม)
class LoginModel(BaseModel):
    email: str
    password: str

# API สำหรับเข้าสู่ระบบ (แก้ไขใหม่เพื่อใช้ REST API)
@app.post("/login")
async def login(data: LoginModel):
    # ใส่ Web API Key ที่คัดลอกมา
    REST_API_KEY = "AIzaSyBa-bZ3RLSN0eGgrCa6g0CKJUx0woP3GHo"
    
    # URL ของ Firebase Auth REST API สำหรับ sign in
    rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={REST_API_KEY}"
    
    # ข้อมูลที่จะส่งไปใน request body
    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True
    }
    
    try:
        # ยิง POST request ไปยัง Firebase
        response = requests.post(rest_api_url, json=payload)
        
        # แปลงคำตอบกลับจาก Firebase เป็น JSON
        response_data = response.json()

        # ถ้า Firebase ตอบกลับมาว่ามี Error (เช่น รหัสผ่านผิด)
        if "error" in response_data:
            error_message = response_data["error"]["message"]
            # แปลง Error message ให้เป็นมิตรกับผู้ใช้มากขึ้น
            if error_message == "INVALID_LOGIN_CREDENTIALS":
                raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")
            else:
                raise HTTPException(status_code=400, detail=error_message)

        # ถ้าสำเร็จ ดึงข้อมูล user ที่ได้กลับมา
        uid = response_data['localId']
        user_email = response_data['email']
        
        # ดึงชื่อจาก Firestore (เหมือนเดิม)
        user_info = db.collection("students").document(uid).get()
        user_display_name = "ผู้ใช้"
        if user_info.exists:
            user_display_name = f"{user_info.to_dict().get('first_name', '')} {user_info.to_dict().get('last_name', '')}"

        # เช็คว่าเป็นอีเมลของอาจารย์หรือไม่
        is_teacher = user_email == "silar@kmitl.ac.th"

        # ส่งข้อมูลกลับไปให้ Frontend
        return {
            "id": uid,
            "name": user_display_name,
            "email": user_email,
            "isTeacher": is_teacher
        }

    except requests.exceptions.RequestException as e:
        # กรณีเชื่อมต่อกับ Firebase ไม่ได้
        raise HTTPException(status_code=500, detail=f"ไม่สามารถเชื่อมต่อกับบริการยืนยันตัวตนได้: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/")
async def get_dashboard_data():
    try:
        # ดึงข้อมูลการเข้าเรียนล่าสุด
        print("Fetching dashboard data...") # เพิ่ม log
        
        # 1. ดึงข้อมูลการเข้าเรียนล่าสุด
        attendances_ref = db.collection("attendances").order_by(
            "timestamp", direction=firestore.Query.DESCENDING
        ).limit(5).stream()
        
        recent_attendances = []
        on_time_count = 0
        late_count = 0
        absent_count = 0
        
        # 2. จัดการข้อมูลสำหรับกราฟ
        labels = ["8:00", "9:00", "10:00", "11:00"]
        datasets = [{
            "label": "จำนวนนักเรียน",
            "data": [0, 0, 0, 0],
            "backgroundColor": "rgba(53, 162, 235, 0.5)",
        }]
        
        # 3. แปลงข้อมูลจาก Firestore
        for doc in attendances_ref:
            data = doc.to_dict()
            attendance_time = data.get("timestamp", 0)
            
            # ดึงข้อมูลนักเรียน
            student = db.collection("students").document(str(data.get("attendee_id"))).get()
            if student.exists:
                student_data = student.to_dict()
                data.update({
                    "first_name": student_data.get("first_name"),
                    "last_name": student_data.get("last_name"),
                    "datetime": attendance_time,  # ย้ายมาไว้ในส่วนนี้
                    "attendee_id": data.get("attendee_id")
                })
                recent_attendances.append(data)
                
                # นับจำนวนตามเวลา
                hour = datetime.fromtimestamp(attendance_time).hour
                if 8 <= hour < 10:
                    on_time_count += 1
                elif 10 <= hour < 11:
                    late_count += 1
                else:
                    absent_count += 1

        # 4. สร้าง response data
        attendance_counts = [
            {"status": "on_time", "count": on_time_count},
            {"status": "late", "count": late_count},
            {"status": "absent", "count": absent_count}
        ]

        attendance_data = {
            "labels": labels,
            "datasets": datasets
        }

        return {
            "attendanceData": attendance_data,
            "attendanceCounts": attendance_counts,
            "recentAttendances": recent_attendances
        }
        
    except Exception as e:
        print(f"Error in dashboard: {str(e)}") # เพิ่ม log
        raise HTTPException(status_code=500, detail=str(e))
