from fastapi import FastAPI
from pydantic import BaseModel

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