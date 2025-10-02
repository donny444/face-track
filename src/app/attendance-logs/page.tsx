"use client";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row } from "react-bootstrap";
import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";
import { ThemeEnum } from "@/interfaces/enums";
import Link from "next/link";

// Mock data
const mockAttendances = [
	{
		datetime: "2025-09-29T08:15:00",
		first_name: "สมชาย",
		last_name: "ใจดี",
	},
	{
		datetime: "2025-09-29T08:30:00",
		first_name: "สมหญิง",
		last_name: "รักเรียน",
	},
	{
		datetime: "2025-09-29T10:15:00",
		first_name: "วิชัย",
		last_name: "ขยันดี",
	},
	{
		datetime: "2025-09-29T11:30:00",
		first_name: "มานี",
		last_name: "มีสุข",
	},
	{
		datetime: "2025-09-29T08:45:00",
		first_name: "สุดา",
		last_name: "ตั้งใจ",
	},
];

export default function AttendanceLogs() {
	const theme = useSelector((state: RootState) => state.theme.mode);
	const startClassTime = new Date().setHours(8, 0, 0, 0);
	const lateClassTime = new Date().setHours(10, 0, 0, 0);
	const endClassTime = new Date().setHours(11, 0, 0, 0);

	const attendanceRows = mockAttendances.map((attendance, index) => {
		const attendanceTime = new Date(attendance.datetime).getTime();
		return (
			<tr key={index}>
				<td>
					{new Date(attendance.datetime).toLocaleString("th-TH", {
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