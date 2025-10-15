import { ThemeEnum } from "./enums.ts";

export interface AttendanceCountsProps {
  countData: Array<AttendanceCountsType>,
  themeMode: ThemeEnum
}

export type AttendanceCountsArray = Array<AttendanceCountsType | null>;

export type AttendanceCountsType = {
  status: string,
  count: number
}