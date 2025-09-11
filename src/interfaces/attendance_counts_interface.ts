import { ThemeEnum } from "./enums.ts";

export default interface AttendanceCountsProps {
  countData: Array<AttendanceCountsType>,
  themeMode: ThemeEnum
}

type AttendanceCountsType = {
  status: string,
  count: number
}