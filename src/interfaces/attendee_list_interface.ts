import AttendeeInterface from "./attendee_interface.ts";
import { ThemeEnum } from "./enums.ts";

export default interface AttendeeListProps {
  attendees: Array<AttendeeInterface>;
  themeMode: ThemeEnum;
}