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
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN")
TOKEN_TTL_MINUTES = int(os.getenv("JWT_TOKEN_TTL_MINUTES"))
VALID_EMAIL_DOMAIN = os.getenv("VALID_EMAIL_DOMAIN")
if not (CLIENT_ORIGIN and TOKEN_TTL_MINUTES):
		CLIENT_ORIGIN = "http://localhost:3000"
		TOKEN_TTL_MINUTES = 60
		raise RuntimeWarning("environment variables not found")
if not VALID_EMAIL_DOMAIN:
		raise RuntimeError("VALID_EMAIL_DOMAIN is required to be set in `.env.local`")

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_ORIGIN],  # หรือ domain ของ frontend
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
	email: str = Form(...)
	first_name: str = Form(...)
	last_name: str = Form(...)
	password: str = Form(...)
	image: Optional[UploadFile] = File(None)

class Instructor(BaseModel):
	email: str | None = None
	first_name: str | None = None
	last_name: str | None = None
	password: str | None = None

# Receive and save attendance data from face recognition
@app.post("/attendances/", status_code=status.HTTP_201_CREATED)
async def Attend(attendance: Attendance):
	attendeeId = attendance.attendee_id
	if not attendeeId:
		raise HTTPException(status_code=400, detail="attendeeId is required in the request body")

	timestamp = attendance.timestamp
	if timestamp == 0:
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

	if existedAttendance is not None and len(list(existedAttendance)) > 0:
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
	if (student.email is None) or (student.password is None):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required for registration")
	
	# First name and last name are mandatory for Firestore
	if (student.first_name is None) or (student.last_name is None):
		raise HTTPException(status_code=400, detail="First name and last name are required for registration")
	
	if "@" not in student.email or not student.email.endswith(VALID_EMAIL_DOMAIN):
		raise HTTPException(status_code=400, detail=f"Email must be from the {VALID_EMAIL_DOMAIN} domain")
	
	studentId = student.email.split("@")[0]

	existingStudentRef = db.collection("students").document(studentId)
	existingStudent = existingStudentRef.get()
	if existingStudent.exists:
		raise HTTPException(status_code=400, detail="Student already exists")

	if student.image:
		if not student.image.content_type in ["image/jpeg", "image/jpg", "image/png"]:
			raise HTTPException(status_code=400, detail="Only .jpg and .png files are supported")
		try:
			# Define the folder to save files
			UPLOAD_DIR = "faces"
			os.makedirs(UPLOAD_DIR, exist_ok=True) # Create folder if it doesn't exist

			# Create a unique filename
			file_extension = student.image.filename.split('.')[-1]
			unique_filename = f"{studentId}.{file_extension}"
			file_location = os.path.join(UPLOAD_DIR, unique_filename)
			
			# Save the file to the specified folder
			with open(file_location, "wb+") as file_object:
				shutil.copyfileobj(student.image.file, file_object)
			
			print(f"File saved locally at: {file_location}")
		except Exception as e:
			raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")
	

	# Create user in Firebase Authentication
	try:
		auth.create_user(
			uid=studentId,
			email=student.email,
			password=student.password,
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))
	
	studentName = {
		"first_name": studentDict["first_name"],
		"last_name": studentDict["last_name"],
	}
	
	studentRef = db.collection("students").document(studentId)
	studentRef.set(studentName)

	return { "message": "Student registered successfully" }

# Login (for instructor)
@app.post("/instructors/", status_code=status.HTTP_200_OK)
async def Login(instructor: Instructor):
	if (instructor.email is None) or (instructor.password is None):
		raise HTTPException(status_code=400, detail="Email and password are required for login")

	try:
		auth.get_user_by_email(instructor.email)
	except auth.UserNotFoundError:
		raise HTTPException(status_code=404, detail="User not found")
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

	instructorDocs = list(
		db.collection("instructors")
		.where("email", "==", instructor.email)
		.limit(1)
		.stream()
	)
	if not instructorDocs:
		raise HTTPException(status_code=404, detail="Instructor not found")

	instructorDoc = instructorDocs[0]
	tokenPayload = {
		"sub": instructorDoc.id,
		"email": instructor.email,
		"iat": int(datetime.now(tz=timezone.utc).timestamp()),
		"exp": int((datetime.now(tz=timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
	}

	token = jwt.encode(tokenPayload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

	instructorDict = instructorDoc.to_dict()
	instructor = Instructor(
		first_name=instructorDict.get("first_name"),
		last_name=instructorDict.get("last_name"),
	)
	instructorDict = instructor.model_dump()

	return {
		"message": "successfully login as an instructor",
		"data": instructorDict,
		"token": token
	}

# Remove a student from Firebase (instructor access)
@app.delete("/students/{studentId}", status_code=status.HTTP_200_OK)
async def Remove(studentId: str):
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

# --- 1. แก้ไขและตั้งค่า Static Files ให้ถูกต้อง ---
# สร้างโฟลเดอร์ชื่อ 'public_uploads' ในโปรเจกต์ของคุณ
# ถ้ามี request มาที่ URL /uploaded_images/... ให้ไปหาไฟล์ในโฟลเดอร์ public_uploads
app.mount("/faces", StaticFiles(directory="faces"), name="static")

# Get all attendance records from the start of the week
@app.get("/insights/")
async def GetAttendancesThisWeek():
	try:
		now = datetime.now(tz=timezone.utc)
		startOfTheWeek = int((now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
		endOfTheWeek = int((now + timedelta(days=6 - now.weekday())).replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())

		attendancesThisWeek = (db.collection("attendances") \
			.select(["timestamp"]) \
			.where(filter=FieldFilter("timestamp", ">=", startOfTheWeek)) \
			.where(filter=FieldFilter("timestamp", "<=", endOfTheWeek)) \
			.order_by("timestamp", direction=firestore.Query.DESCENDING) \
			.stream() \
		)
		attendances = list(attendance.to_dict()["timestamp"] for attendance in attendancesThisWeek)

		return {
			"message": "Attendances from the start of the week retrieved successfully",
			"data": attendances
		}

	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
