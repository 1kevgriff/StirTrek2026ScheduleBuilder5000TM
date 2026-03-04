# Speaker Preferences

These preferences are included in the scheduling prompt sent to Claude.
Edit this file to adjust speaker constraints before generating a new schedule.

## Room Sizing

Room tiers for reference:
- **Large**: Room 1 (388), Room 5 (340)
- **Medium**: Room 2 (314), Room 6 (293), Room 4 (234), Room 3 (228)
- **Small**: Room 7 (224), Room 8 (173)

### Large Room Preferences

These speakers had 150+ attendance in 2025 and should be in Rooms 1 or 5:

- **Kathryn Grayson Nanz** — 2025 peak: 210 attendees
- **Guy Royse** — 2025 peak: 200 attendees
- **Cory House** — 2025 peak: 196 attendees
- **Matt Eland** (listed as "Matthew-Hope Eland" in 2026 data) — 2025 peak: 157 attendees
- **Jeff McWherter** — 2025 peak: 154 attendees

### Medium Room Preferences

These speakers had 100-149 attendance in 2025 and should prefer Rooms 2 or 6:

- **Tristan Chiappisi** — 2025 peak: 133 attendees
- **Barret Blake** — 2025 peak: 101 attendees

## Time Slot Preferences

Slot reference: morning = slots 1-4 (08:30-12:15), afternoon = slots 5-7 (02:00-04:45)

- **Chris DeMars** — both sessions before noon (slots 1-4)
- **Kate Holterhoff** — morning only (slots 1-4), flight departure at 7:00 PM

## Unavailable Slots

_(No unavailability constraints currently set. Add entries like:)_
<!-- - **Speaker Name** — unavailable for slot_1, slot_7 -->

## Scheduling Conflicts (Avoid Against)

These speakers should NOT be scheduled in the same time slot as each other:

_(No conflict preferences currently set. Add entries like:)_
<!-- - **Speaker A** should not compete with **Speaker B** (similar topics) -->

## Session Ordering

These sessions should be scheduled in a specific order within the day:

- **Hazel Bohon** — "Microservices for Pragmatists" should be scheduled BEFORE "Boiling The Frog: Implementing a Modern Message Based Architecture Without Anyone Noticing" (the first talk covers general microservices/distributed architecture; the second focuses specifically on messaging patterns)

## Additional Notes

- AI/ML sessions from new speakers should go in Rooms 1-5 (AI is the hottest track)
- Architecture sessions should go in Rooms 2-6
- Niche/specialized sessions should go in Rooms 7 or 8
- New speakers with unknown draw should go in middle rooms (3, 4, 6, 7)
