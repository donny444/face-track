"use client";

import { useEffect, useState } from "react";

import axios from "axios";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row, Modal } from "react-bootstrap";

import { BackButton } from "../components/buttons.tsx";

import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../contexts/store";
import { login } from "../contexts/store/auth_slice.ts";

import { AttendeesType } from "@/interfaces/attendee_interface";
import { ThemeEnum, AttendanceStatusEnum } from "@/interfaces/enums";

import { GetAttendanceStatus } from "../helpers/attendance_helper.ts";

import { SERVER_URL } from '@/data/global_variables.ts';

export default function StudentList() {
  const dispatch = useDispatch();
  const theme = useSelector(
    (state: RootState) => state.theme.mode
  ) as RootState["theme"]["mode"];
  const isAuthenticated = useSelector(
    (state: RootState) => state.auth.isAuthenticated
  ) as RootState["auth"]["isAuthenticated"];

  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);

  const [data, setData] = useState<AttendeesType>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const token = sessionStorage.getItem("token");
  if (token && !isAuthenticated) {
    dispatch(
      login({
        first_name: sessionStorage.getItem("first_name") || "",
        last_name: sessionStorage.getItem("last_name") || "",
        token: token,
      })
    );
  }

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${SERVER_URL}/students/`);
      const responseBody = response.data;
      if (response.status !== 200) {
        setError(responseBody.detail);
        console.error(error);
      }
      setData(responseBody.data);
      console.log(responseBody.message);
    } catch (error) {
      console.error("Error fetching students:", error);
      setError("ไม่สามารถโหลดข้อมูลได้");
    } finally {
      setLoading(false);
    }
  };

  // ดึงข้อมูลนักเรียน
  useEffect(() => {
    fetchStudents();
  }, []);

  const handleDelete = (studentId: string) => {
    // เช็คว่าเป็นอาจารย์หรือไม่
    if (isAuthenticated === false) {
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
          `${SERVER_URL}/students/${selectedStudent}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const responseBody = response.data;

        if (response.status !== 200) {
          setError(responseBody.detail);
          console.error(error);
        }
        fetchStudents();
        console.log(responseBody.message);
      } catch (error) {
        console.error("Error deleting student:", error);
        if (axios.isAxiosError(error)) {
          const errorMessage =
            error.response?.data?.detail || "ไม่สามารถลบข้อมูลได้";
          alert(errorMessage);
        }
      } finally {
        setShowConfirmModal(false);
        setSelectedStudent(null);
      }
    }
  };

  const studentRows = (): JSX.Element => {
    const rows: JSX.Element[] = [];
    for (const student of data) {
      const timestamp = student.timestamp * 1000;
      const attendanceStatus = GetAttendanceStatus(timestamp);
      rows.push(
        <tr key={student.attendee_id}>
          <td>{student.attendee_id}</td>
          <td>
            {student.first_name} {student.last_name}
          </td>
          {timestamp === 0 ? (
            <>
              <td className="text-secondary">-</td>
              <td className="text-secondary">-</td>
            </>
          ) : (
            <>
              <td>
                {new Date(timestamp).toLocaleString("th-TH", {
                  hour: "2-digit",
                  minute: "2-digit"
                })}
              </td>
              {attendanceStatus === AttendanceStatusEnum.ON_TIME ? (
                <td className="text-success">ตรงเวลา</td>
              ) : null}
              {attendanceStatus === AttendanceStatusEnum.LATE ? (
                <td className="text-warning">เข้าสาย</td>
              ) : null}
              {attendanceStatus === AttendanceStatusEnum.ABSENT ? (
                <td className="text-danger">ขาด</td>
              ) : null}
            </>
          )}
          {isAuthenticated ? (
          	<td className="text-center">
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDelete(student.attendee_id)}
              >
                ลบ
              </Button>
          	</td>
          ) : (
            <></>
          )}
        </tr>
      );
    }
		return <>{rows}</>;
  };

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
          <BackButton />
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
              theme === ThemeEnum.DARK ? "bg-dark text-white" : "bg-light"
            } p-4 rounded`}
          >
            <table
              className={`table table-striped ${
                theme === ThemeEnum.DARK ? "table-dark" : "table-light"
              }`}
            >
              <thead>
                <tr>
                  <th>รหัสนักเรียน</th>
                  <th>ชื่อ - นามสกุล</th>
                  <th>เวลา</th>
                  <th>สถานะ</th>
									{isAuthenticated ?
                  	<th className="text-center">จัดการ</th>
										: <></>
									}
                </tr>
              </thead>
              <tbody>{studentRows()}</tbody>
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
          className={theme === ThemeEnum.DARK ? "bg-dark text-white" : ""}
        >
          <Modal.Title>ยืนยันการลบ</Modal.Title>
        </Modal.Header>
        <Modal.Body
          className={theme === ThemeEnum.DARK ? "bg-dark text-white" : ""}
        >
          คุณต้องการลบรายชื่อนักเรียนคนนี้ใช่หรือไม่?
        </Modal.Body>
        <Modal.Footer
          className={theme === ThemeEnum.DARK ? "bg-dark text-white" : ""}
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
