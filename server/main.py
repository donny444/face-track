from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import firebase_admin
from firebase_admin import auth, credentials, firestore
from datetime import datetime, timezone
from google.cloud.firestore_v1 import FieldFilter

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()
db = firestore.client()

class Attendance(BaseModel):
	attendee_id: str
	timestamp: int

class Student(BaseModel):
	student_id: str
	first_name: str
	last_name: str
	email: str | None = None
	password: str | None = None

@app.post("/attendances/")
async def Attend(attendance: Attendance):
	attendanceDict = attendance.model_dump()


	# Convert timestamp to UTC date (year, month, day)
	attendance_date = datetime.fromtimestamp(attendanceDict["timestamp"], tz=timezone.utc).date()
	startOfToday = int(datetime(attendance_date.year, attendance_date.month, attendance_date.day, tzinfo=timezone.utc).timestamp())
	endOfToday = int(datetime(attendance_date.year, attendance_date.month, attendance_date.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())

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
		user = auth.create_user(
			uid=studentDict["email"].split("@")[0],
			email=studentDict["email"],
			password=studentDict["password"],
		)
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

	existingStudentRef = db.collection("students").document(studentDict["student_id"])

	existingStudent = existingStudentRef.get()
	
	if existingStudent:
		raise HTTPException(status_code=400, detail="Student already exists")
	
	studentRef = db.collection("students").document(studentDict["student_id"])
	studentRef.set(
		{
			"first_name": studentDict["first_name"],
			"last_name": studentDict["last_name"],
		}
	)

	return studentDict, status.HTTP_201_CREATED

@app.delete("/students/")
async def Remove(studentId: str):
	# Delete user from Firebase Authentication
	try:
		auth.delete_user(f"{studentId}")
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))
	
	# Delete student and their attendances from Firestore
	transaction = db.transaction()
	transaction.delete(db.collection("attendances").where("attendee_id", "==", studentId).stream())
	transaction.delete(db.collection("students").document(studentId))
	transaction.commit()

	return studentId, status.HTTP_204_NO_CONTENT