"use client";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row, Modal } from "react-bootstrap";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";
import { ThemeEnum } from "@/interfaces/enums";
import Link from "next/link";
import axios from "axios";

interface Student {
	student_id: string;
	first_name: string;
	last_name: string;
}

const mockStudents = [
	{
		student_id: "6501234",
		first_name: "สมชาย",
		last_name: "ใจดี",
	},
	{
		student_id: "6501235",
		first_name: "สมหญิง",
		last_name: "รักเรียน",
	},
	{
		student_id: "6501236",
		first_name: "วิชัย",
		last_name: "ขยันดี",
	},
	{
		student_id: "6501237",
		first_name: "มานี",
		last_name: "มีสุข",
	},
	{
		student_id: "6501238",
		first_name: "สุดา",
		last_name: "ตั้งใจ",
	},
];

export default function StudentList() {
	const router = useRouter();
	const theme = useSelector((state: RootState) => state.theme.mode);
	const auth = useSelector((state: RootState) => state.auth) as RootState["auth"];
	const [showConfirmModal, setShowConfirmModal] = useState(false);
	const [selectedStudent, setSelectedStudent] = useState<string | null>(null);
	const [students, setStudents] = useState<Student[]>(mockStudents);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState("");

	// เช็ค authentication
	useEffect(() => {
		if (!auth.isAuthenticated || !auth.user) {
			router.push("/login");
			return;
		}
	}, [auth.isAuthenticated, auth.user, router]);

	// ดึงข้อมูลนักเรียน
	useEffect(() => {
		const fetchStudents = async () => {
			try {
				const response = await axios.get("http://localhost:8000/students/");
				setStudents(response.data);
			} catch (error) {
				console.error("Error fetching students:", error);
				setError("ไม่สามารถโหลดข้อมูลได้");
			} finally {
				setLoading(false);
			}
		};

		fetchStudents();
	}, []);

	const handleDelete = (studentId: string) => {
		// เช็คว่าเป็นอาจารย์หรือไม่
		if (!auth.user?.isTeacher) {
			alert("คุณไม่มีสิทธิ์ลบรายชื่อนักเรียน");
			return;
		}
		setSelectedStudent(studentId);
		setShowConfirmModal(true);
	};

	const confirmDelete = async () => {
		if (selectedStudent) {
			try {
				// เปลี่ยนวิธีการส่ง studentId
				const response = await axios.delete(
					`http://localhost:8000/students/${selectedStudent}`
				);

				if (response.status === 200) {
					setStudents(
						students.filter(
							(student) => student.student_id !== selectedStudent
						)
					);
					setShowConfirmModal(false);
					setSelectedStudent(null);
				}
			} catch (error) {
				console.error("Error deleting student:", error);
				if (axios.isAxiosError(error)) {
					const errorMessage =
						error.response?.data?.detail || "ไม่สามารถลบข้อมูลได้";
					alert(errorMessage);
				}
			}
		}
	};

	const studentRows = students.map((student, index) => (
		<tr key={index}>
			<td>{student.student_id}</td>
			<td>{student.first_name}</td>
			<td>{student.last_name}</td>
			<td className="text-center">
				<Button
					variant="danger"
					size="sm"
					onClick={() => handleDelete(student.student_id)}
				>
					ลบ
				</Button>
			</td>
		</tr>
	));

	// ถ้ายังไม่ authenticated ให้แสดงหน้าว่าง
	if (!auth.isAuthenticated || !auth.user) {
		return null;
	}

	// แสดงผลขณะโหลดข้อมูล
	if (loading) {
		return (
			<Container fluid className="mt-4">
				<div className="text-center">กำลังโหลดข้อมูล...</div>
			</Container>
		);
	}

	// แสดงผลเมื่อเกิดข้อผิดพลาด
	if (error) {
		return (
			<Container fluid className="mt-4">
				<div className="text-center text-danger">{error}</div>
			</Container>
		);
	}

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
									<th>ชื่อ</th>
									<th>นามสกุล</th>
									<th className="text-center">จัดการ</th>
								</tr>
							</thead>
							<tbody>{studentRows}</tbody>
						</table>
					</div>
				</Col>
			</Row>

			{/* Modal ยืนยันการลบ */}
			<Modal
				show={showConfirmModal}
				onHide={() => setShowConfirmModal(false)}
				centered
			>
				<Modal.Header
					closeButton
					className={
						theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
					}
				>
					<Modal.Title>ยืนยันการลบ</Modal.Title>
				</Modal.Header>
				<Modal.Body
					className={
						theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
					}
				>
					คุณต้องการลบรายชื่อนักเรียนคนนี้ใช่หรือไม่?
				</Modal.Body>
				<Modal.Footer
					className={
						theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
					}
				>
					<Button
						variant="secondary"
						onClick={() => setShowConfirmModal(false)}
					>
						ยกเลิก
					</Button>
					<Button variant="danger" onClick={confirmDelete}>
						ยืนยันการลบ
					</Button>
				</Modal.Footer>
			</Modal>
		</Container>
	);
}