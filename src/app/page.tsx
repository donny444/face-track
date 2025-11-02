"use client";

import { useState, useEffect, useMemo } from "react";

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
  ChartData,
  ChartOptions,
} from "chart.js";
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);
ChartJS.defaults.color = "#ffffff";

import attendanceData from "@/data/weekly_attendances.json";

import {
  AttendeeInterface,
  AttendeesType,
} from "@/interfaces/attendee_interface.ts";
import { ThemeEnum, AttendanceStatusEnum } from "@/interfaces/enums.ts";

import { GetAttendanceStatus } from "./helpers/attendance_helper.ts";

import { SERVER_URL } from "@/data/global_variables.ts";

export default function Summary() {
  const theme = useSelector((state: RootState) => state.theme.mode);

  return (
    <Container fluid={"md"}>
      <Row>
        <AttendanceCountSummary themeMode={theme} />
        <WeeklyChartSummary themeMode={theme} />
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
    const response = await axios.get(`${SERVER_URL}/attendances/?recent=false`);
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  const countStatuses = () => {
    let inTimeCount = 0;
    let lateCount = 0;
    let absentCount = 0;

    for (let i = 0; i < data.length; i++) {
      const timestamp = data[i].timestamp * 1000;
      const attendanceStatus = GetAttendanceStatus(timestamp);
      switch (attendanceStatus) {
        case AttendanceStatusEnum.ON_TIME:
          inTimeCount++;
          break;
        case AttendanceStatusEnum.LATE:
          lateCount++;
          break;
        case AttendanceStatusEnum.ABSENT:
          absentCount++;
          break;
        case undefined:
          break;
        default:
          break;
      }
    }

    setIntime(inTimeCount);
    setLate(lateCount);
    setAbsent(absentCount);
  };

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

function WeeklyChartSummary({ themeMode }: { themeMode: ThemeEnum }) {
  const [textColor, setTextColor] = useState("white");
  const [onTimeCounts, setOnTimeCounts] = useState<number[]>(Array(7).fill(0));
  const [lateCounts, setLateCounts] = useState<number[]>(Array(7).fill(0));
  const [absentCounts, setAbsentCounts] = useState<number[]>(Array(7).fill(0));
  const chartData = useMemo<ChartData<"bar">>(
    () => ({
      labels: attendanceData.labels,
      datasets: [
        { ...attendanceData.datasets[0], data: onTimeCounts },
        { ...attendanceData.datasets[1], data: lateCounts },
        { ...attendanceData.datasets[2], data: absentCounts },
      ],
    }),
    [onTimeCounts, lateCounts, absentCounts],
  );
  const [data, setData] = useState<number[]>([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const nextTextColor = themeMode === ThemeEnum.DARK ? "white" : "black";

    setTextColor(nextTextColor);
  }, [themeMode]);

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

  const insightResponse = async () => {
    const response = await axios.get(`${SERVER_URL}/insights/`);
    const responseBody = await response.data;
    if (response.status !== 200) {
      setError(responseBody.detail);
      console.error(error);
    }
    setData(responseBody.data);
    console.log(responseBody.message);
  };

  useEffect(() => {
    insightResponse();
  }, []);

  useEffect(() => {
    if (data.length === 0) {
      setOnTimeCounts(Array(7).fill(0));
      setLateCounts(Array(7).fill(0));
      setAbsentCounts(Array(7).fill(0));
      return;
    }

    const nextOnTimeCounts = Array(7).fill(0);
    const nextLateCounts = Array(7).fill(0);
    const nextAbsentCounts = Array(7).fill(0);

    for (let i = 0; i < data.length; i++) {
      const epoch = data[i] * 1000;
      const attendanceStatus = GetAttendanceStatus(epoch);
      const day = new Date(epoch).getDay(); // 0 (Sun) - 6 (Sat)

      switch (attendanceStatus) {
        case AttendanceStatusEnum.ON_TIME:
          nextOnTimeCounts[day]++;
          break;
        case AttendanceStatusEnum.LATE:
          nextLateCounts[day]++;
          break;
        case AttendanceStatusEnum.ABSENT:
          nextAbsentCounts[day]++;
          break;
        case undefined:
          break;
        default:
          break;
      }
    }

    setOnTimeCounts(nextOnTimeCounts);
    setLateCounts(nextLateCounts);
    setAbsentCounts(nextAbsentCounts);
  }, [data]);

  const options: ChartOptions<"bar"> = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: "Weekly Chart",
        font: {
          size: 18,
        },
        color: textColor,
      },
      legend: {
        labels: { color: textColor },
      },
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: textColor },
      },
      y: {
        stacked: true,
        ticks: { color: textColor },
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
    const response = await axios.get(`${SERVER_URL}/attendances/?recent=true`);
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
        const attendanceStatus = GetAttendanceStatus(timestamp);
        result[i] = (
          <tr key={attendance.attendee_id}>
            <td>
              {new Date(timestamp).toLocaleString("th-TH", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </td>
            <td>
              {attendance.first_name} {attendance.last_name}
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
    const response = await axios.get(`${SERVER_URL}/students/?head=true`);
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
        const attendanceStatus = GetAttendanceStatus(timestamp);
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
                    minute: "2-digit",
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
