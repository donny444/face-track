"use client";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row } from "react-bootstrap";
import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";
import { ThemeEnum } from "@/interfaces/enums";
import Link from "next/link";

// Mock data
const mockStudents = [
	{
		student_id: "6501234",
		first_name: "สมชาย",
		last_name: "ใจดี",
		class: "ม.4/1",
	},
	{
		student_id: "6501235",
		first_name: "สมหญิง",
		last_name: "รักเรียน",
		class: "ม.4/2",
	},
	{
		student_id: "6501236",
		first_name: "วิชัย",
		last_name: "ขยันดี",
		class: "ม.4/3",
	},
	{
		student_id: "6501237",
		first_name: "มานี",
		last_name: "มีสุข",
		class: "ม.4/4",
	},
	{
		student_id: "6501238",
		first_name: "สุดา",
		last_name: "ตั้งใจ",
		class: "ม.4/5",
	},
];

export default function StudentList() {
	const theme = useSelector((state: RootState) => state.theme.mode);

	const studentRows = mockStudents.map((student, index) => (
		<tr key={index}>
			<td>{student.student_id}</td>
			<td>
				{student.first_name} {student.last_name}
			</td>
			<td>{student.class}</td>
		</tr>
	));

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
						รายชื่อนักเรียนทั้งหมด
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
									<th>รหัสนักเรียน</th>
									<th>ชื่อ - สกุล</th>
									<th>ชั้นเรียน</th>
								</tr>
							</thead>
							<tbody>{studentRows}</tbody>
						</table>
					</div>
				</Col>
			</Row>
		</Container>
	);
}