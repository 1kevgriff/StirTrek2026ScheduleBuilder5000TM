# Rules for Scheduling Stir Trek 2026

## Data
Session data is in the data/stir-trek-2026-accepted.xlsx file.

## Day Schedule

| Time | Event |
|------|-------|
| 07:30am - 08:30am | Breakfast |
| 08:30am - 09:15am | Session Slot 1 (8 sessions) |
| 09:30am - 10:15am | Session Slot 2 (8 sessions) |
| 10:30am - 11:15am | Session Slot 3 (8 sessions) |
| 11:30am - 12:15pm | Session Slot 4 (8 sessions) |
| 12:15pm - 01:00pm | Lunch |
| 01:00pm - 01:45pm | Pending |
| 02:00pm - 02:45pm | Session Slot 5 (8 sessions) |
| 03:00pm - 03:45pm | Session Slot 6 (8 sessions) |
| 04:00pm - 04:45pm | Session Slot 7 (8 sessions) |
| 05:00pm - 06:00pm | Movie Trailers |

## Room Capacities

Each "room" is a live theater that simulcasts to overflow theaters.

| Room | Total Capacity | Live Theater | Simulcasting To |
|------|---------------|--------------|-----------------|
| 1    | 388           | Theater 14   | Theaters 12, 13 |
| 2    | 314           | Theater 15   | Theaters 10, 11 |
| 3    | 228           | Theater 16   | Theater 21       |
| 4    | 234           | Theater 17   | Theater 20       |
| 5    | 340           | Theater 4    | Theaters 5,6,7,8,9 |
| 6    | 293           | Theater 3    | Theaters 1, 2    |
| 7    | 224           | Theater 27   | Theaters 23,24,25,26 |
| 8    | 173           | Theater 28   | Theaters 18, 19  |

Rooms sorted by capacity: 1 (388) > 5 (340) > 2 (314) > 6 (293) > 4 (234) > 3 (228) > 7 (224) > 8 (173)

## Scheduling Rules
* There are 8 rooms with varying capacities (see above).
* Each session is 45 minutes long with 15-minute breaks between slots.
* 7 session slots x 8 rooms = 56 cells for 56 sessions.
* Each room can have only one session at a time.
* A presenter can present only one session at a time.
* Review tracks and topics. Don't assign two sessions of the same track at the same time.
* Place higher-draw sessions (popular tracks, well-known speakers) in larger rooms.

## Output Rules
* CSV format
* Header row: Time, Room 1 (388), Room 2 (314), ..., Room 8 (173)
* Include breakfast, lunch, pending, and movie trailer rows
* Session cells contain "Title - Speaker"

## Speaker Considerations
* 7 speakers have 2 sessions each — they must be in different time slots.
