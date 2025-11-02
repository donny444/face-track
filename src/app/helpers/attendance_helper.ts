import { AttendanceStatusEnum } from "@/interfaces/enums.ts";

export function GetAttendanceStatus(timestamp: number): AttendanceStatusEnum | undefined {
  const startClassTime = new Date(timestamp).setHours(9, 0, 0, 0);
  const lateClassTime = new Date(timestamp).setHours(9, 15, 0, 0);
  const endClassTime = new Date(timestamp).setHours(10, 0, 0, 0);

  if (timestamp >= endClassTime) {
    return AttendanceStatusEnum.ABSENT;
  } else if (timestamp >= lateClassTime) {
    return AttendanceStatusEnum.LATE;
  } else if (timestamp >= startClassTime) {
    return AttendanceStatusEnum.ON_TIME;
  } else {
    return undefined;
  }
}