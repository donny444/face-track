from fastapi import FastAPI
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

class Attendance(BaseModel):
	id: str
	firstname: str
	lastname: str
	datetime: str

@app.get("/")
async def root():
	return { "message": "Hello World" }

@app.post("/")
async def Attend(attendance: Attendance):
	return None