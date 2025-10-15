"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import axios from "axios";

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

import attendanceData from "@/data/attendance_data.json";
import attendanceCounts from "@/data/attendance_counts.json";
// import recentAttendances from "@/data/recent_attendances.json";

import DailyChartProps from "@/interfaces/daily_chart_interface";
import {
  AttendanceCountsProps,
  AttendanceCountsArray,
} from "@/interfaces/attendance_counts_interface.ts";
// import AttendanceLogProps from "@/interfaces/attendance_log_interface.ts";
// import AttendeeListProps from "@/interfaces/attendee_list_interface.ts";
import {
  AttendeeInterface,
  AttendeesType,
} from "@/interfaces/attendee_interface.ts";
import { ThemeEnum } from "@/interfaces/enums.ts";

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
      <Row className="mb-3">
        <Col className="d-flex justify-content-end">
          <Link href="/register">
            <Button variant="primary" className="me-2">
              Register
            </Button>
          </Link>
        </Col>
      </Row>
      <Row>
        <AttendanceCountSummary
          countData={attendanceCounts}
          themeMode={theme}
        />
        <DailyChartSummary chartData={attendanceData} themeMode={theme} />
      </Row>
      <Row>
        <AttendanceLogSummary themeMode={theme} />
        <AttendeeListSummary themeMode={theme} />
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({
  countData,
  themeMode,
}: AttendanceCountsProps) {
  const [data, setData] = useState<AttendanceCountsArray>([]);
  const [error, setError] = useState(null);

  let themeBootstrap = "";
  switch (themeMode) {
    case ThemeEnum.DARK:
      themeBootstrap = "bg-dark text-white";
      break;
    case ThemeEnum.LIGHT:
      themeBootstrap = "bg-light text-black";
      break;
    default:
      break;
  }

  const countResponse = async () => {
    const response = await axios.get("http://localhost:8000/counts/");
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  useEffect(() => {
    countResponse();
  }, []);

  return (
    <Col md={4} className={`${themeBootstrap} p-2 rounded`}>
      <p className="fs-4 ms-2">สรุปบันทึกการเข้าเรียน</p>
      {error && <p className="text-danger">{error}</p>}
      {data && (
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
      )}
    </Col>
  );
}

function DailyChartSummary({ chartData, themeMode }: DailyChartProps) {
  let themeBootstrap = "";
  switch (themeMode) {
    case ThemeEnum.DARK:
      themeBootstrap = "bg-dark text-white";
      break;
    case ThemeEnum.LIGHT:
      themeBootstrap = "bg-light text-black";
      break;
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

function AttendanceLogSummary({ themeMode }: { themeMode: ThemeEnum }) {
  const [data, setData] = useState<AttendeesType>([]);
  const [error, setError] = useState(null);

  const attendanceResponse = async () => {
    const response = await axios.get(
      "http://localhost:8000/attendances/?recent=true"
    );
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  useEffect(() => {
    attendanceResponse();
  }, []);

  const startClassTime = new Date().setHours(8, 0, 0, 0);
  const lateClassTime = new Date().setHours(10, 0, 0, 0);
  const endClassTime = new Date().setHours(11, 0, 0, 0);

  // const attendeesLength = data.length;

  const attendanceRows = (): JSX.Element => {
    const result: JSX.Element[] = [];
    for (let i = 0; i <= 4; i++) {
      const attendance: AttendeeInterface = data[i];
      if (attendance) {
        const timestamp = attendance.timestamp * 1000;
        result[i] = (
          <tr key={attendance.attendee_id}>
            <td>
              {new Date(timestamp).toLocaleString("th-TH", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </td>
            <td>
              {attendance.first_name} {attendance.last_name}
            </td>
            {timestamp < lateClassTime && timestamp >= startClassTime ? (
              <td className="text-success">ตรงเวลา</td>
            ) : null}
            {timestamp < endClassTime && timestamp >= lateClassTime ? (
              <td className="text-warning">เข้าสาย</td>
            ) : null}
            {timestamp > endClassTime ? (
              <td className="text-danger">ขาด</td>
            ) : null}
          </tr>
        );
      } else {
        result[i] = (
          <tr>
            <td>-</td>
            <td>-</td>
            <td>-</td>
          </tr>
        );
      }
    }
    return <>{result}</>;
  };

  return (
    <Col
      md={6}
      className={`${
        themeMode === ThemeEnum.DARK
          ? "bg-dark text-white"
          : "bg-light text-black"
      }
      p-2 rounded
    `}
    >
      <Container className="d-flex flex-row justify-content-between">
        <p className="fs-4">บันทึกการเข้าเรียนล่าสุด</p>
        <Link
          href="/attendance-logs"
          className="text-white text-decoration-none"
        >
          <Button>Expand</Button>
        </Link>
      </Container>
      <table
        className={`table table-striped 
        ${themeMode === ThemeEnum.DARK ? "table-dark" : "table-light"}
      `}
      >
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

function AttendeeListSummary({ themeMode }: { themeMode: ThemeEnum }) {
  const [data, setData] = useState<AttendeesType>([]);
  const [error, setError] = useState(null);

  const studentsResponse = async () => {
    const response = await axios.get(
      "http://localhost:8000/students/?head=true"
    );
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  useEffect(() => {
    studentsResponse();
  }, []);

  const startClassTime = new Date().setHours(8, 0, 0, 0);
  const lateClassTime = new Date().setHours(10, 0, 0, 0);
  const endClassTime = new Date().setHours(11, 0, 0, 0);

  const attendanceRows = (): JSX.Element => {
    const result: JSX.Element[] = [];
    for (let i = 0; i < 5; i++) {
      const attendee: AttendeeInterface = data[i];
      if (attendee) {
        const timestamp = attendee.timestamp * 1000;
        result[i] = (
          <tr key={i}>
            <td>{attendee.attendee_id}</td>
            <td>
              {attendee.first_name} {attendee.last_name}
            </td>
            {timestamp === 0 ? (
              <>
                <td className="text-secondary">-</td>
                <td className="text-secondary">-</td>
              </>
            ) : (
              <>
                <td>
                  {new Date(attendee.timestamp).toLocaleString("th-TH", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </td>
                {timestamp < lateClassTime && timestamp >= startClassTime ? (
                  <td className="text-success">ตรงเวลา</td>
                ) : null}
                {timestamp < endClassTime && timestamp >= lateClassTime ? (
                  <td className="text-warning">เข้าสาย</td>
                ) : null}
                {timestamp > endClassTime ? (
                  <td className="text-danger">ขาด</td>
                ) : null}
              </>
            )}
          </tr>
        );
      } else {
        result[i] = (
          <tr>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
          </tr>
        );
      }
    }
    return <>{result}</>;
  };

  return (
    <Col
      md={6}
      className={`${
        themeMode === ThemeEnum.DARK
          ? "bg-dark text-white"
          : "bg-light text-black"
      }
      p-2 rounded
    `}
    >
      <Container className="d-flex flex-row justify-content-between">
        <p className="fs-4">รายการนักศึกษาในวิชาเรียน</p>
        <Link href="/student-list" className="text-white text-decoration-none">
          <Button>Expand</Button>
        </Link>
      </Container>
      <table
        className={`table table-striped 
        ${themeMode === ThemeEnum.DARK ? "table-dark" : "table-light"}
      `}
      >
        <thead>
          <tr>
            <th>รหัสนักศึกษา</th>
            <th>ชื่อ - สกุล</th>
            <th>เวลา</th>
            <th>สถานะ</th>
          </tr>
        </thead>
        {error && <p className="text-danger">{error}</p>}
        {data && <tbody>{attendanceRows()}</tbody>}
      </table>
    </Col>
  );
}
