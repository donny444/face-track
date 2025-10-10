"use client";

import Link from "next/link";

// import styles from "./page.module.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Button, Col, Container, Row } from "react-bootstrap";

import { useSelector } from "react-redux";
import { RootState } from "./contexts/store";

import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);
ChartJS.defaults.color = "#ffffff";

// import attendanceData from "@/data/attendance_data.json";
// import attendanceCounts from "@/data/attendance_counts.json";
// import recentAttendances from "@/data/recent_attendances.json";

import DailyChartProps from "@/interfaces/daily_chart_interface";
import AttendanceCountsProps from "@/interfaces/attendance_counts_interface.ts";
import AttendanceLogProps from "@/interfaces/attendance_log_interface.ts";
import { ThemeEnum } from "@/interfaces/enums.ts"
import { useEffect, useState } from "react";
import axios from "axios";

interface Student {
  student_id: string;
  first_name: string;
  last_name: string;
}

export default function Summary() {
  const theme = useSelector((state: RootState) => state.theme.mode);
  const [realTimeData, setRealTimeData] = useState({
  attendanceData: [],
  attendanceCounts: [],
  recentAttendances: []
});
const [students, setStudents] = useState<Student[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState("");

useEffect(() => {
  const fetchData = async () => {
    try {
      const [dashboardResponse, studentsResponse, attendancesResponse] = await Promise.all([
        axios.get("http://localhost:8000/dashboard/"),
        axios.get("http://localhost:8000/students/"),
        axios.get("http://localhost:8000/attendances/")
      ]);

       setRealTimeData({
        attendanceData: dashboardResponse.data.attendanceData,
        attendanceCounts: dashboardResponse.data.attendanceCounts,
        recentAttendances: attendancesResponse.data.slice(-5)
      });
      // รวมข้อมูล dashboard และ attendance
      setRealTimeData({
        attendanceData: dashboardResponse.data.attendanceData,
        attendanceCounts: dashboardResponse.data.attendanceCounts,
        recentAttendances: attendancesResponse.data.slice(-5)
      });
      setStudents(studentsResponse.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      setError("ไม่สามารถโหลดข้อมูลได้");
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, []);


  if (loading) {
    return <div>กำลังโหลดข้อมูล...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <Container fluid={"md"}>
      <Row>
        <AttendanceCountSummary 
          countData={realTimeData.attendanceCounts} 
          themeMode={theme} 
        />
        <DailyChartSummary 
          chartData={realTimeData.attendanceData} 
          themeMode={theme} 
        />
      </Row>
      <Row>
        <AttendanceLogSummary 
          attendees={realTimeData.recentAttendances} 
          themeMode={theme} 
        />
        <AttendeeListSummary 
          attendees={students} 
          themeMode={theme} 
        />
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({ countData, themeMode }: AttendanceCountsProps) {
  let themeBootstrap = "";
  switch (themeMode) {
    case ThemeEnum.DARK:
      themeBootstrap = "bg-dark text-white";break;
    case ThemeEnum.LIGHT:
      themeBootstrap = "bg-light text-black";break;
    default:
      break;
  }
  
  return (
    <Col md={4} className={`${themeBootstrap} p-2 rounded`}>
      <p className="fs-4 ms-2">สรุปบันทึกการเข้าเรียน</p>
      <Container className="d-flex flex-column justify-content-evenly h-75">
        <p className="text-success fs-5 d-flex justify-content-between">
          <span>เข้าตรงเวลา</span>
          <span>{countData[0].count} คน</span>
        </p>
        <p className="text-warning fs-5 d-flex justify-content-between">
          <span>เข้าสาย</span>
          <span>{countData[1].count} คน</span>
        </p>
        <p className="text-danger fs-5 d-flex justify-content-between">
          <span>ขาด</span>
          <span>{countData[2].count} คน</span>
        </p>
      </Container>
    </Col>
  );
}

function DailyChartSummary({ chartData, themeMode }: DailyChartProps) {
  let themeBootstrap = "";
  switch (themeMode) {
    case ThemeEnum.DARK:
      themeBootstrap = "bg-dark text-white";break;
    case ThemeEnum.LIGHT:
      themeBootstrap = "bg-light text-black";break;
    default:
      break;
  }

  const options = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: "กราฟประจำวัน",
        color: "white",
      },
    },
  };

  return (
    <Col md={8} className={`${themeBootstrap} p-2 rounded`}>
      <Bar options={options} data={chartData} />
    </Col>
  );
}

function AttendanceLogSummary({ attendees, themeMode }: AttendanceLogProps) {
  const startClassTime = new Date().setHours(8, 0, 0, 0);
  const lateClassTime = new Date().setHours(10, 0, 0, 0);
  const endClassTime = new Date().setHours(11, 0, 0, 0);

  const attendeesLength = attendees.length;

  const attendanceRows = (): JSX.Element => {
    const result: JSX.Element[] = [];
    for (let i = attendeesLength - 1; i >= 0; i--) {
      const attendance = attendees[i];
      const attendanceTime = new Date(attendance.datetime).getTime();
      const index = attendeesLength - 1 - i;
      result[index] = (
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
          {attendanceTime < endClassTime && attendanceTime >= lateClassTime ? (
            <td className="text-warning">เข้าสาย</td>
          ) : null}
          {attendanceTime > endClassTime ? (
            <td className="text-danger">ขาด</td>
          ) : null}
        </tr>
      );
    }
    return <>{result}</>;
  };

  return (
    <Col md={6} className={`${themeMode === ThemeEnum.DARK
      ? "bg-dark text-white"
      : "bg-light text-black"}
      p-2 rounded
    `}>
      <Container className="d-flex flex-row justify-content-between">
        <p className="fs-4">บันทึกการเข้าเรียนล่าสุด</p>
        <Button>
          <Link href="/attendance-logs" className="text-white text-decoration-none">
            Expand
          </Link>
        </Button>
      </Container>
      <table className={`table table-striped 
        ${themeMode === ThemeEnum.DARK ? "table-dark" : "table-light"}
      `}>
        <thead>
          <tr>
            <th>เวลา</th>
            <th>ชื่อ - สกุล</th>
            <th>สถานะ</th>
          </tr>
        </thead>
        <tbody>{attendanceRows()}</tbody>
      </table>
    </Col>
  );
}

// แก้ไข interface และ component AttendeeListSummary
interface AttendeeListProps {
  attendees: Student[];
  themeMode: string;
}

function AttendeeListSummary({ attendees, themeMode }: AttendeeListProps) {
  const studentRows = attendees.slice(0, 5).map((student, index) => (
    <tr key={index}>
      <td>{student.student_id}</td>
      <td>
        {student.first_name} {student.last_name}
      </td>
    </tr>
  ));

  return (
    <Col md={6}>
      <div className={`p-3 ${themeMode === ThemeEnum.DARK ? 'bg-dark text-white' : 'bg-light'} rounded`}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">รายชื่อนักศึกษา</h5>
          <Link href="/student-list">
            <Button variant={themeMode === ThemeEnum.DARK ? 'light' : 'primary'} size="sm">
              Expand
            </Button>
          </Link>
        </div>
        <table className={`table ${themeMode === ThemeEnum.DARK ? 'table-dark' : ''}`}>
          <thead>
            <tr>
              <th>รหัสนักศึกษา</th>
              <th>ชื่อ-นามสกุล</th>
            </tr>
          </thead>
          <tbody>
            {studentRows}
          </tbody>
        </table>
      </div>
    </Col>
  );
}
