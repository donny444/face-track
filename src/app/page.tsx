"use client";

// import styles from "./page.module.css";
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

import attendanceData from "@/data/attendance_data.json";
import attendanceCounts from "@/data/attendance_counts.json";
import recentAttendances from "@/data/recent_attendances.json";

import BarChartInterface from "@/interfaces/bar_chart_interface.ts";
import AttendanceCountsInterface from "@/interfaces/attendance_counts_interface.ts";

export default function Summary() {
  return (
    <Container>
      <Row>
        <AttendanceCountSummary countData={attendanceCounts} />
        <DailyChartSummary chartData={attendanceData} />
      </Row>
      <Row>
        <AttendanceLogSummary />
        <AttendeeListSummary />
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({ countData }: AttendanceCountsInterface) {
  return (
    <Col>
      <p>เข้าตรงเวลา: {countData[0].count}</p>
      <p>เข้าสาย: {countData[1].count}</p>
      <p>ขาด: {countData[2].count}</p>
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
      },
    },
  };

  return (
    <Col>
      <Bar options={options} data={chartData} />;
    </Col>
  );
}

function AttendanceLogSummary() {
  const startClassTime = new Date().setHours(8, 0, 0, 0);
  const lateClassTime = new Date().setHours(10, 0, 0, 0);
  const endClassTime = new Date().setHours(11, 0, 0, 0);

  const attendeesLength = recentAttendances.length;

  const attendanceRows = (): JSX.Element => {
    const result: JSX.Element[] = [];
    for (let i = attendeesLength - 1; i >= 0; i--) {
      const attendance = recentAttendances[i];
      const attendanceTime = new Date(attendance.datetime).getTime();
      result[attendeesLength - i] = (
        <tr key={i}>
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
          {attendanceTime > endClassTime ? <td className="text-danger">ขาด</td> : null}
        </tr>
      );
    }
    return <>{result}</>;
  };

  return (
    <table>
      <thead>
        <tr>
          <th>เวลา</th>
          <th>ชื่อ - สกุล</th>
          <th>สถานะ</th>
        </tr>
      </thead>
      <tbody>{attendanceRows()}</tbody>
    </table>
  );
}

function AttendeeListSummary() {
  return <Col></Col>;
}
