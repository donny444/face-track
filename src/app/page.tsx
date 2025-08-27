"use client";

import styles from "./page.module.css";
import "bootstrap/dist/css/bootstrap.min.css";
import { Col, Container, Row } from "react-bootstrap";
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
import recentAttendances from "@/data/recent_attendances.json";

import BarChartInterface from "@/interfaces/bar_chart_interface.ts";
import AttendanceCountsInterface from "@/interfaces/attendance_counts_interface.ts";
import AttendeeInterface from "@/interfaces/attendee_interface.ts";

export default function Summary() {
  return (
    <Container fluid={"md"}>
      <Row>
        <AttendanceCountSummary countData={attendanceCounts} />
        <DailyChartSummary chartData={attendanceData} />
      </Row>
      <Row>
        <AttendanceLogSummary attendees={recentAttendances} />
        <AttendeeListSummary attendees={recentAttendances} />
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({ countData }: AttendanceCountsInterface) {
  return (
    <Col md={4} className="bg-dark text-white p-2 rounded">
      <p className="fs-4 ms-2">สรุปบันทึกการเข้าออก</p>
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

interface DailyChartProps {
  chartData: BarChartInterface;
}

function DailyChartSummary({ chartData }: DailyChartProps) {
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
    <Col md={8} className="bg-dark text-white p-2 rounded">
      <Bar options={options} data={chartData} />
    </Col>
  );
}

interface AttendeesInterface {
  attendees: Array<AttendeeInterface>;
}

function AttendanceLogSummary({ attendees }: AttendeesInterface) {
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
    <Col md={6} className="bg-dark text-white p-2 rounded">
      <table className="table table-dark table-striped">
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

function AttendeeListSummary({ attendees }: AttendeesInterface) {
  const startClassTime = new Date().setHours(8, 0, 0, 0);
  const lateClassTime = new Date().setHours(10, 0, 0, 0);
  const endClassTime = new Date().setHours(11, 0, 0, 0);

  const attendanceRows = (): JSX.Element => {
    const result: JSX.Element[] = [];
    for (let i = 0; i < 5; i++) {
      const attendee = attendees[i];
      const attendanceTime = new Date(attendee.datetime).getTime();
      result[i] = (
        <tr key={i}>
          <td>{attendee.id}</td>
          <td>
            {attendee.first_name} {attendee.last_name}
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
          <td>
            {new Date(attendee.datetime).toLocaleString("th-TH", {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </td>
        </tr>
      );
    }
    return <>{result}</>;
  };

  return (
    <Col md={6} className="bg-dark text-white p-2 rounded">
      <table className="table table-dark table-striped">
        <thead>
          <tr>
            <th>เลขที่</th>
            <th>ชื่อ - สกุล</th>
            <th>เวลา</th>
            <th>สถานะ</th>
          </tr>
        </thead>
        <tbody>{attendanceRows()}</tbody>
      </table>
    </Col>
  );
}
