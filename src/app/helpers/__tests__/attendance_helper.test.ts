import { GetAttendanceStatus } from "../attendance_helper";
import { AttendanceStatusEnum } from "@/interfaces/enums";

/**
 * The helper uses the local timezone of the runtime to compute the 09:00 /
 * 09:15 / 10:00 cutoffs.  Building timestamps with `new Date(y, m, d, h, min)`
 * also uses the local timezone, so the comparisons are stable regardless of
 * the host TZ.
 */
function timestampAt(hour: number, minute: number): number {
  return new Date(2025, 0, 15, hour, minute, 0, 0).getTime();
}

describe("GetAttendanceStatus", () => {
  it("returns undefined before 09:00", () => {
    expect(GetAttendanceStatus(timestampAt(8, 59))).toBeUndefined();
    expect(GetAttendanceStatus(timestampAt(0, 0))).toBeUndefined();
  });

  it("returns ON_TIME between 09:00 and 09:14:59", () => {
    expect(GetAttendanceStatus(timestampAt(9, 0))).toBe(AttendanceStatusEnum.ON_TIME);
    expect(GetAttendanceStatus(timestampAt(9, 14))).toBe(AttendanceStatusEnum.ON_TIME);
  });

  it("returns LATE between 09:15 and 09:59:59", () => {
    expect(GetAttendanceStatus(timestampAt(9, 15))).toBe(AttendanceStatusEnum.LATE);
    expect(GetAttendanceStatus(timestampAt(9, 59))).toBe(AttendanceStatusEnum.LATE);
  });

  it("returns ABSENT at or after 10:00", () => {
    expect(GetAttendanceStatus(timestampAt(10, 0))).toBe(AttendanceStatusEnum.ABSENT);
    expect(GetAttendanceStatus(timestampAt(23, 59))).toBe(AttendanceStatusEnum.ABSENT);
  });
});
