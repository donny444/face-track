export type AttendeesType = Array<AttendeeInterface>;

export interface AttendeeInterface {
  attendee_id: string;
  timestamp: number;
  first_name: string;
  last_name: string;
}