"use client";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row, Alert } from "react-bootstrap";
import { useEffect, useState } from "react";
import axios from "axios";
import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";
import { ThemeEnum } from "@/interfaces/enums";
import Link from "next/link";

interface Attendance {
	attendee_id: string;
	timestamp: number;
	first_name?: string;
	last_name?: string;
}

export default function AttendanceLogs() {
	const theme = useSelector((state: RootState) => state.theme.mode);
	const [attendances, setAttendances] = useState<Attendance[]>([]);
	const [error, setError] = useState<string>("");

	useEffect(() => {
		const fetchAttendances = async () => {
			try {
				const response = await axios.get("http://localhost:8000/attendances/");
				setAttendances(response.data);
			} catch (error) {
				console.error("Error fetching attendances:", error);
				setError("ไม่สามารถโหลดข้อมูลได้");
			}
		};
		fetchAttendances();
	}, []);

	const startClassTime = new Date().setHours(8, 0, 0, 0);
	const lateClassTime = new Date().setHours(10, 0, 0, 0);
	const endClassTime = new Date().setHours(11, 0, 0, 0);

	const attendanceRows = attendances.map((attendance, index) => {
		const attendanceTime = attendance.timestamp * 1000; // Convert to milliseconds
		return (
			<tr key={index}>
				<td>
					{new Date(attendanceTime).toLocaleString("th-TH", {
						hour: "2-digit",
						minute: "2-digit",
						second: "2-digit",
					})}
				</td>
				<td>
					{attendance.first_name} {attendance.last_name}
				</td>
				{attendanceTime < lateClassTime &&
				attendanceTime >= startClassTime ? (
					<td className="text-success">ตรงเวลา</td>
				) : null}
				{attendanceTime < endClassTime &&
				attendanceTime >= lateClassTime ? (
					<td className="text-warning">เข้าสาย</td>
				) : null}
				{attendanceTime > endClassTime ? (
					<td className="text-danger">ขาด</td>
				) : null}
			</tr>
		);
	});

	return (
		<Container fluid className="mt-4">
			{error && (
				<Row>
					<Col>
						<Alert
							variant="danger"
							dismissible
							onClose={() => setError("")}
						>
							{error}
						</Alert>
					</Col>
				</Row>
			)}
			<Row className="mb-3">
				<Col>
					<Link href="/">
						<Button variant="secondary">← กลับ</Button>
					</Link>
				</Col>
				<Col>
					<h2
						className={`text-center ${
							theme === ThemeEnum.DARK ? "text-white" : "text-dark"
						}`}
					>
						บันทึกการเข้าเรียนทั้งหมด
					</h2>
				</Col>
				<Col></Col>
			</Row>
			<Row>
				<Col>
					<div
						className={`${
							theme === ThemeEnum.DARK
								? "bg-dark text-white"
								: "bg-light"
						} p-4 rounded`}
					>
						<table
							className={`table table-striped ${
								theme === ThemeEnum.DARK
									? "table-dark"
									: "table-light"
							}`}
						>
							<thead>
								<tr>
									<th>เวลา</th>
									<th>ชื่อ - สกุล</th>
									<th>สถานะ</th>
								</tr>
							</thead>
							<tbody>{attendanceRows}</tbody>
						</table>
					</div>
				</Col>
			</Row>
		</Container>
	);
}