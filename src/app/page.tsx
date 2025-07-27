"use client"

// import styles from "./page.module.css";
import { Col, Container, Row } from "react-bootstrap";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
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

import BarChartInterface from "@/interfaces/bar_chart_interface.ts";
import AttendanceCountsInterface from "@/interfaces/attendance_counts_interface.ts";

export default function Summary() {
  return (
    <Container>
      <Row>
        <Col>
          <AttendanceCountSummary countData={attendanceCounts} />
        </Col>
        <Col>
          <DailyChartSummary chartData={attendanceData} />
        </Col>
      </Row>
      <Row>
        <Col>
          <AttendanceLogSummary />
        </Col>
        <Col>
          <AttendeeListSummary />
        </Col>
      </Row>
    </Container>
  );
}

function AttendanceCountSummary({ countData }: AttendanceCountsInterface) {
  return (
    <div>
      <p>เข้าตรงเวลา: {countData[0].count}</p>
      <p>เข้าสาย: {countData[1].count}</p>
      <p>ขาด: {countData[2].count}</p>
    </div>
  );
}

interface DailyChartProps {
  chartData: BarChartInterface
}
function DailyChartSummary({ chartData }: DailyChartProps) {
  const options = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: "กราฟประจำวัน"
      }
    }
  }

  return (
    <Bar options={options} data={chartData} /> 
  );
}

function AttendanceLogSummary() {
  return (
    <div>

    </div>
  );
}

function AttendeeListSummary() {
  return (
    <div>

    </div>
  );
}