"use client";

import { useEffect, useState } from "react";

import axios from "axios";

import "bootstrap/dist/css/bootstrap.min.css";
import { Col, Container, Row, Alert } from "react-bootstrap";

import { BackButton } from "../components/buttons";

import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";

import { startClassTime, lateClassTime, endClassTime } from "@/data/attendance_times.ts";

import { AttendeesType } from "@/interfaces/attendee_interface";
import { ThemeEnum } from "@/interfaces/enums";

export default function AttendanceLogs() {
	const theme = useSelector((state: RootState) => state.theme.mode);
	const [data, setData] = useState<AttendeesType>([]);
	const [error, setError] = useState<string>("");

	useEffect(() => {
		const fetchAttendances = async () => {
			try {
				const response = await axios.get("http://localhost:8000/attendances/?recent=false");
				const responseBody = response.data;
				if (response.status !== 200) {
					setError(responseBody.detail);
					console.error(error);
				}
				setData(responseBody.data);
				console.log(responseBody.message);
			} catch (error) {
				console.error("Error fetching attendances:", error);
				setError("ไม่สามารถโหลดข้อมูลได้");
			}
		};
		fetchAttendances();
	}, []);

	const attendanceRows = data.map((attendance, index) => {
		const timestamp = attendance.timestamp * 1000;
		return (
			<tr key={index}>
				<td>
					{new Date(timestamp).toLocaleString("th-TH", {
						hour: "2-digit",
						minute: "2-digit"
					})}
				</td>
				<td>
					{attendance.first_name} {attendance.last_name}
				</td>
				{timestamp < lateClassTime &&
				timestamp >= startClassTime ? (
					<td className="text-success">ตรงเวลา</td>
				) : null}
				{timestamp < endClassTime &&
				timestamp >= lateClassTime ? (
					<td className="text-warning">เข้าสาย</td>
				) : null}
				{timestamp > endClassTime ? (
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
					<BackButton />
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
									<th>ชื่อ - นามสกุล</th>
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