import AttendeeInterface from "./attendee_interface.ts";
import { ThemeEnum } from "./enums.ts";

export default interface AttendanceLogProps {
  attendees: Array<AttendeeInterface>;
  themeMode: ThemeEnum;
}