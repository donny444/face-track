"use client";

import { useState, useEffect } from "react";

import axios from "axios";

// import styles from "./page.module.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Col, Container, Row } from "react-bootstrap";

import { ExpandButton } from "./components/buttons";

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
import { startClassTime, lateClassTime, endClassTime } from "@/data/attendance_times.ts";

import DailyChartProps from "@/interfaces/daily_chart_interface";
import { AttendeeInterface, AttendeesType } from "@/interfaces/attendee_interface.ts";
import { ThemeEnum } from "@/interfaces/enums.ts";

export default function Summary() {
  const theme = useSelector((state: RootState) => state.theme.mode);

  return (
    <Container fluid={"md"}>
      <Row>
        <AttendanceCountSummary themeMode={theme} />
        <DailyChartSummary chartData={attendanceData} themeMode={theme} />
      </Row>
      <Row>
        <AttendanceLogSummary themeMode={theme} />
        <StudentListSummary themeMode={theme} />
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({ themeMode }: { themeMode: ThemeEnum }) {
  const [data, setData] = useState<AttendeesType>([]);
  const [error, setError] = useState(null);
  const [inTime, setIntime] = useState(0);
  const [late, setLate] = useState(0);
  const [absent, setAbsent] = useState(0);

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

  const attendanceResponse = async () => {
    const response = await axios.get("http://localhost:8000/attendances/?recent=false");
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  const countStatuses = () => {
    console.log("countStatuses invoked");

    let inTimeCount = 0;
    let lateCount = 0;
    let absentCount = 0;

    for (let i = 0; i < data.length; i++) {
      const timestamp = data[i].timestamp * 1000;
      if (timestamp < lateClassTime && timestamp >= startClassTime) {
        inTimeCount++;
      } else if (timestamp < endClassTime && timestamp >= lateClassTime) {
        lateCount++;
      } else if (timestamp > endClassTime) {
        absentCount++;
      }
    }

    setIntime(inTimeCount);
    setLate(lateCount);
    setAbsent(absentCount);

    console.log(`inTime: ${inTime}, late: ${late}, absent: ${absent}`);
  }

  useEffect(() => {
    attendanceResponse();
  }, []);
  
  useEffect(() => {
    if (data.length > 0) {
      countStatuses();
    }
  }, [data]);

  return (
    <Col md={4} className={`${themeBootstrap} p-2 rounded`}>
      <p className="fs-4 ms-2">สรุปบันทึกการเข้าเรียน</p>
      {error && <p className="text-danger">{error}</p>}
      {data && (
        <Container className="d-flex flex-column justify-content-evenly h-75">
          <p className="text-success fs-5 d-flex justify-content-between">
            <span>เข้าตรงเวลา</span>
            <span>{inTime} คน</span>
          </p>
          <p className="text-warning fs-5 d-flex justify-content-between">
            <span>เข้าสาย</span>
            <span>{late} คน</span>
          </p>
          <p className="text-danger fs-5 d-flex justify-content-between">
            <span>ขาด</span>
            <span>{absent} คน</span>
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
                minute: "2-digit"
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
        <ExpandButton to="/attendance-logs" />
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

function StudentListSummary({ themeMode }: { themeMode: ThemeEnum }) {
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
                  {new Date(timestamp).toLocaleString("th-TH", {
                    hour: "2-digit",
                    minute: "2-digit"
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
        <ExpandButton to="student-list" />
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
