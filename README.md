# Stir Trek 2026 Schedule Builder 5000

An AI-powered schedule optimizer for [Stir Trek 2026](https://stirtrek.com) that assigns 56 sessions across 7 time slots and 8 rooms, using Claude to intelligently balance track diversity, speaker constraints, room capacity, and historical attendance data.

**Live schedule:** [https://1kevgriff.github.io/StirTrek2026ScheduleBuilder5000TM/output/schedule.html](https://1kevgriff.github.io/StirTrek2026ScheduleBuilder5000TM/output/schedule.html)

## How It Works

1. **Load** session data from the accepted sessions spreadsheet (56 sessions, 10 tracks, 49 speakers)
2. **Generate** an optimized schedule using Claude CLI in headless mode, considering:
   - Hard constraints: no speaker conflicts, all sessions placed, 8 per slot
   - Soft constraints: track distribution, room sizing by attendance history, topic variety
3. **Validate** the result against all constraints
4. **Output** CSV, JSON, and an interactive HTML schedule

## Features

- **Attendance-aware room assignments** — 2025 attendance data drives room sizing for returning speakers
- **Schedule versioning** — every generation is saved; HTML lets you compare versions with diff highlighting
- **Drag-and-drop scheduling** — rearrange sessions in the HTML view with real-time speaker conflict validation
- **Community proposals** — drag sessions around, click "Propose Changes", and a GitHub Issue is created automatically. A GitHub Action validates the proposal and opens a PR.
- **Track filtering** — filter the schedule view by track
- **Print-friendly** — clean print layout with no UI chrome

## Quick Start

```bash
pip install -r requirements.txt

# Full run: generate schedule via Claude CLI
python schedule_builder.py

# Just print the prompt (no CLI call)
python schedule_builder.py --prompt

# Use a previously saved schedule
python schedule_builder.py --from-json output/schedule.json

# Regenerate HTML from existing versions
python schedule_builder.py --html-only
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--prompt` | Print the scheduling prompt and exit |
| `--from-json FILE` | Skip Claude CLI; load schedule from a JSON file |
| `--version-label LABEL` | Label for this schedule version |
| `--version-desc DESC` | Description for this schedule version |
| `--html-only` | Regenerate HTML from existing `versions.json` |

## Project Structure

```
.
├── data/
│   └── stir-trek-2026-accepted.xlsx   # Source: accepted sessions
├── output/
│   ├── schedule.json                  # Latest schedule (slot → session IDs)
│   ├── versions.json                  # All schedule versions with metadata
│   ├── schedule.csv                   # CSV for spreadsheet import
│   └── schedule.html                  # Interactive HTML schedule
├── templates/
│   └── schedule_template.html         # HTML template with placeholders
├── .github/
│   ├── workflows/process-swap.yml     # Action: validate issue → create PR
│   └── scripts/process_swap.py        # Extract + validate swap from issue
├── schedule_builder.py                # Main script
├── rules.md                           # Scheduling rules and room capacities
└── requirements.txt                   # Just openpyxl
```

## Room Capacity

| Room | Capacity | Live Theater | Simulcast |
|------|----------|-------------|-----------|
| Room 1 | 388 | Theater 14 | Theaters 12, 13 |
| Room 2 | 314 | Theater 15 | Theaters 10, 11 |
| Room 5 | 340 | Theater 4 | Theaters 5, 6, 7, 8, 9 |
| Room 6 | 293 | Theater 3 | Theaters 1, 2 |
| Room 3 | 228 | Theater 16 | Theater 21 |
| Room 4 | 234 | Theater 17 | Theater 20 |
| Room 7 | 224 | Theater 27 | Theaters 23, 24, 25, 26 |
| Room 8 | 173 | Theater 28 | Theaters 18, 19 |

**Total capacity per slot: 2,194 seats**

## Proposing Schedule Changes

Anyone can propose changes without needing special permissions:

1. Open the [live schedule](https://1kevgriff.github.io/StirTrek2026ScheduleBuilder5000TM/output/schedule.html)
2. Drag sessions to swap them (speaker conflicts are blocked automatically)
3. Click **Propose Changes** — a pre-filled GitHub Issue opens
4. Submit the issue — a GitHub Action validates the schedule and creates a PR
5. A maintainer reviews and merges

## Day Schedule

| Time | Event |
|------|-------|
| 07:30 - 08:30 | Breakfast |
| 08:30 - 09:15 | Session Slot 1 |
| 09:30 - 10:15 | Session Slot 2 |
| 10:30 - 11:15 | Session Slot 3 |
| 11:30 - 12:15 | Session Slot 4 |
| 12:15 - 01:00 | Lunch |
| 01:00 - 01:45 | Pending |
| 02:00 - 02:45 | Session Slot 5 |
| 03:00 - 03:45 | Session Slot 6 |
| 04:00 - 04:45 | Session Slot 7 |
| 05:00 - 06:00 | Movie Trailers |

## Dependencies

- Python 3.10+
- `openpyxl` — Excel file reading
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) — for schedule generation (not needed for `--from-json` or `--html-only`)
