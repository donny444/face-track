export default interface AttendanceCountsInterface {
  countData: Array<AttendanceCountsType>
}

type AttendanceCountsType = {
  status: string,
  count: number
}