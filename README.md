# FaceTrack

## Stack

- **Client:** Next.js, Chart.js, Redux, Bootstrap.
- **Server:** Python, FastAPI, Firebase.
- **Face detection:** Raspberry Pi, OpenCV.
- **Miscellaneous:** RealVNC.

## API Endpoints

| Method | Path | Description | Request Body | Query Parameters |
| --- | --- | --- | --- | --- |
| **`POST`**  | `/attendances/`  | Receive and save attendance data from face recognition. | `{
  "attendee_id": string,
  "timestamp": int
}` | `-` |
| **`DELETE`**  | `/attendances/`  | Remove a student from Firebase (instructor access.) | `{
  "student_id": string
}` | `-` |
| **`GET`**  | `/attendances/` | Receive attendance log (recent/today) for displaying. | `-` | `recent: boolean`, |
| **`GET`**  | `/students/` | Receive student list (head/all) for displaying (searching included.) | `-` | `head: boolean`,
`search: string`, |
| **`GET`**  | `/statuses/`  | Return counts of attendance statuses. | `-`  | `-` |
| **`GET`**  | `/chart/`  | Return today’s attendance data that is used to form the chart. | `-`  | `-` |

## Resources

https://www.canva.com/design/DAGtgfRDLZg/_M7O38SNMZHAOUfjCm4F_w/edit

https://www.canva.com/design/DAGwbRT7zuA/RK5Wl46dvlmOa-1ZqA5Ktw/edit

https://github.com/donny444/face-track

https://pypi.org/project/firebase/

https://firebase.google.com/docs/reference/admin/python

https://console.firebase.google.com/project/face-track-b68c8/overview

https://youtu.be/k38K-atV_UM