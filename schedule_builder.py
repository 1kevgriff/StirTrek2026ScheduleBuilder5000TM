#!/usr/bin/env python3
"""
Stir Trek 2026 Schedule Builder

Generates a scheduling prompt from session data, sends it to the Claude CLI
in headless mode, validates the result, and writes a CSV schedule.

Usage:
    python schedule_builder.py              # full run: prompt -> claude -> validate -> csv
    python schedule_builder.py --prompt     # just print the prompt (no CLI call)
    python schedule_builder.py --from-json output/schedule.json   # skip CLI, use saved JSON
"""

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Force UTF-8 on Windows so emoji/special chars in session data don't crash
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from openpyxl import load_workbook
except ImportError:
    print("Missing dependency. Run: pip install -r requirements.txt")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "stir-trek-2026-accepted.xlsx"
OUTPUT_DIR = BASE_DIR / "output"
CSV_PATH = OUTPUT_DIR / "schedule.csv"
JSON_PATH = OUTPUT_DIR / "schedule.json"
VERSIONS_PATH = OUTPUT_DIR / "versions.json"
HTML_PATH = OUTPUT_DIR / "schedule.html"
TEMPLATE_PATH = BASE_DIR / "templates" / "schedule_template.html"

SLOT_TIMES = [
    "08:30am - 09:15am",
    "09:30am - 10:15am",
    "10:30am - 11:15am",
    "11:30am - 12:15pm",
    "02:00pm - 02:45pm",
    "03:00pm - 03:45pm",
    "04:00pm - 04:45pm",
]

ROOMS = [
    {"num": 1, "alias": "Room 1",  "capacity": 388, "live": "Theater 14", "simulcast": "Theaters 12, 13"},
    {"num": 2, "alias": "Room 2",  "capacity": 314, "live": "Theater 15", "simulcast": "Theaters 10, 11"},
    {"num": 3, "alias": "Room 3",  "capacity": 228, "live": "Theater 16", "simulcast": "Theater 21"},
    {"num": 4, "alias": "Room 4",  "capacity": 234, "live": "Theater 17", "simulcast": "Theater 20"},
    {"num": 5, "alias": "Room 5",  "capacity": 340, "live": "Theater 4",  "simulcast": "Theaters 5,6,7,8,9"},
    {"num": 6, "alias": "Room 6",  "capacity": 293, "live": "Theater 3",  "simulcast": "Theaters 1, 2"},
    {"num": 7, "alias": "Room 7",  "capacity": 224, "live": "Theater 27", "simulcast": "Theaters 23,24,25,26"},
    {"num": 8, "alias": "Room 8",  "capacity": 173, "live": "Theater 28", "simulcast": "Theaters 18, 19"},
]

ROOM_NAMES = [f"{r['alias']} ({r['capacity']})" for r in ROOMS]

# 2025 attendance data: speaker name -> peak attendance from last year
# Used to inform room sizing for returning speakers
ATTENDANCE_2025 = {
    "Kathryn Grayson Nanz": 210,
    "Guy Royse": 200,
    "Cory House": 196,
    "Matt Eland": 157,       # Listed as "Matthew-Hope Eland" in 2026 data
    "Matthew-Hope Eland": 157,
    "Jeff McWherter": 154,
    "Tristan Chiappisi": 133,
    "Barret Blake": 101,
    "Bob Fornal": 88,
    "Randy Pagels": 86,
    "Cameron Presley": 78,
    "Kelly Morrison": 75,
    "Amanda Lange": 74,
    "Sam Basu": 69,
    "Burton Smith": 65,
    "Lance Finney": 55,
    "Brian McKeiver": 48,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sessions():
    wb = load_workbook(EXCEL_PATH, read_only=True)
    ws = wb["Accepted sessions"]

    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    col = {name: i for i, name in enumerate(headers)}

    sessions = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        session_id = row[col["Session Id"]]
        if session_id is None:
            continue
        desc = row[col["Description"]] or ""
        if len(desc) > 200:
            desc = desc[:200] + "..."
        sessions.append({
            "id": str(session_id),
            "title": row[col["Title"]],
            "description": desc,
            "speakers": row[col["Speakers"]],
            "track": row[col["Track"]],
        })

    wb.close()
    return sessions


def find_multi_session_speakers(sessions):
    speaker_sessions = defaultdict(list)
    for s in sessions:
        speaker_sessions[s["speakers"]].append(s["id"])
    return {k: v for k, v in speaker_sessions.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------

def build_prompt(sessions, multi_speakers):
    session_block = "\n".join(
        f"- ID: {s['id']} | Title: {s['title']} | Speaker: {s['speakers']} "
        f"| Track: {s['track']} | Desc: {s['description']}"
        for s in sessions
    )

    speaker_constraint = "\n".join(
        f"  - {speaker}: sessions {', '.join(ids)}"
        for speaker, ids in multi_speakers.items()
    )

    track_counts = Counter(s["track"] for s in sessions)
    track_summary = "\n".join(
        f"  - {t}: {track_counts[t]} sessions"
        for t in sorted(track_counts)
    )

    room_block = "\n".join(
        f"  Position {i} = Room {r['num']}: {r['capacity']} seats "
        f"(live in {r['live']}, simulcast to {r['simulcast']})"
        for i, r in enumerate(ROOMS)
    )

    # Build 2025 attendance info for returning speakers
    attendance_lines = []
    for s in sessions:
        peak = ATTENDANCE_2025.get(s["speakers"])
        if peak:
            attendance_lines.append(
                f"  - {s['speakers']} (session {s['id']}): "
                f"2025 peak attendance = {peak}"
            )
    attendance_block = "\n".join(attendance_lines) if attendance_lines else "  (no data)"

    return f"""You are a conference schedule optimizer for Stir Trek 2026.

TASK: Assign all 56 sessions to 7 time slots with 8 rooms each.
Each slot is an array of 8 session IDs where POSITION MATTERS — position maps to a specific room.

ROOM ASSIGNMENTS (array index -> room):
{room_block}

SESSIONS:
{session_block}

TRACK SUMMARY:
{track_summary}

HARD CONSTRAINTS (must all be satisfied):
1. Exactly 7 time slots (slot_1 through slot_7), each with exactly 8 sessions.
2. Every session ID must appear exactly once across all slots.
3. No speaker may appear in two sessions in the same time slot.
   Multi-session speakers who MUST be in different slots:
{speaker_constraint}

SOFT CONSTRAINTS (optimize for these):
1. Minimize same-track sessions in the same time slot. Spread tracks across slots.
2. Spread popular/large tracks (Application Development, Architecture, AI/ML) across many slots.
3. Consider session descriptions to create variety within each slot — attendees should have diverse choices.
4. ROOM SIZING: Place higher-draw sessions in larger rooms using 2025 attendance data.
   Room sizes: Room 1 (388) > Room 5 (340) > Room 2 (314) > Room 6 (293) > Room 4 (234) > Room 3 (228) > Room 7 (224) > Room 8 (173)

   RETURNING SPEAKER ATTENDANCE FROM 2025 (use this to prioritize room assignments):
{attendance_block}

   Room assignment guidelines based on 2025 data:
   - 150+ attendance -> MUST be in Rooms 1 (388) or 5 (340): Cory House, Kathryn Grayson Nanz, Guy Royse, Matt Eland, Jeff McWherter
   - 100-149 attendance -> Prefer Rooms 2 (314) or 6 (293): Tristan Chiappisi, Barret Blake
   - AI/ML sessions from new speakers -> Rooms 1-5 (AI is the hottest track)
   - Architecture sessions -> Rooms 2-6
   - Niche/specialized sessions -> Rooms 7 (224) or 8 (173)
   - New speakers with unknown draw -> middle rooms (3, 4, 6, 7)

OUTPUT FORMAT:
Return ONLY valid JSON, no other text. Use this exact structure:
{{
  "slot_1": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_2": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_3": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_4": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_5": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_6": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"],
  "slot_7": ["room1_id", "room2_id", "room3_id", "room4_id", "room5_id", "room6_id", "room7_id", "room8_id"]
}}

Each array must contain exactly 8 session IDs as strings. Position 0 = Room 1 (388 seats), Position 7 = Room 8 (173 seats).
Use the exact Session Id values provided above."""


# ---------------------------------------------------------------------------
# Claude CLI interaction
# ---------------------------------------------------------------------------

def call_claude(prompt):
    """Call Claude CLI in headless mode. Returns parsed schedule dict."""
    print("Calling Claude CLI to generate schedule...")

    # Strip CLAUDECODE env var so the CLI doesn't refuse to launch
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    result = subprocess.run(
        ["claude", "-p", "-", "--output-format", "json",
         "--model", "sonnet", "--max-turns", "1"],
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=180,
        env=env,
    )
    # Decode output as UTF-8
    result = subprocess.CompletedProcess(
        result.args, result.returncode,
        stdout=result.stdout.decode("utf-8", errors="replace") if result.stdout else "",
        stderr=result.stderr.decode("utf-8", errors="replace") if result.stderr else "",
    )

    if result.returncode != 0:
        print(f"Claude CLI error (exit {result.returncode}):")
        print(result.stderr)
        sys.exit(1)

    raw = result.stdout.strip()
    if not raw:
        print("Claude CLI returned empty output.")
        if result.stderr:
            print("stderr:", result.stderr[:500])
        sys.exit(1)

    return parse_claude_response(raw)


def parse_claude_response(raw):
    """Extract schedule JSON from Claude CLI's JSON-envelope output."""
    # Parse the outer envelope
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        print("Failed to parse Claude CLI output as JSON.")
        print("Raw output (first 500 chars):", raw[:500])
        sys.exit(1)

    # Extract text content from various envelope shapes
    text = ""
    if isinstance(envelope, dict) and "result" in envelope:
        text = envelope["result"]
    elif isinstance(envelope, list):
        for item in envelope:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                break
    elif isinstance(envelope, str):
        text = envelope
    else:
        text = str(envelope)

    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try extracting from markdown code fences
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON with slot_1 key
    m = re.search(r'(\{\s*"slot_1".*\})', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    print("Could not extract schedule JSON from Claude's response.")
    print("Response text (first 1000 chars):", text[:1000])
    sys.exit(1)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_schedule(schedule, sessions):
    errors = []
    session_map = {s["id"]: s for s in sessions}
    all_ids = set(session_map.keys())

    if len(schedule) != 7:
        errors.append(f"Expected 7 slots, got {len(schedule)}")

    assigned_ids = []
    for slot_name in sorted(schedule.keys()):
        slot_ids = [str(sid) for sid in schedule[slot_name]]
        if len(slot_ids) != 8:
            errors.append(f"{slot_name}: expected 8 sessions, got {len(slot_ids)}")
        assigned_ids.extend(slot_ids)

        speakers_in_slot = []
        for sid in slot_ids:
            if sid in session_map:
                speaker = session_map[sid]["speakers"]
                if speaker in speakers_in_slot:
                    errors.append(
                        f"{slot_name}: speaker '{speaker}' appears twice"
                    )
                speakers_in_slot.append(speaker)
            else:
                errors.append(f"{slot_name}: unknown session ID '{sid}'")

    assigned_set = set(assigned_ids)
    missing = all_ids - assigned_set
    if missing:
        errors.append(f"Missing sessions: {missing}")
    extra = assigned_set - all_ids
    if extra:
        errors.append(f"Unknown session IDs: {extra}")
    dupes = [sid for sid, c in Counter(assigned_ids).items() if c > 1]
    if dupes:
        errors.append(f"Duplicate session IDs: {dupes}")

    return len(errors) == 0, errors


def compute_track_stats(schedule, sessions):
    session_map = {s["id"]: s for s in sessions}
    stats = {}
    total_doublings = 0

    for slot_name in sorted(schedule.keys()):
        tracks = [
            session_map[str(sid)]["track"]
            for sid in schedule[slot_name]
            if str(sid) in session_map
        ]
        counts = Counter(tracks)
        stats[slot_name] = counts
        for c in counts.values():
            if c > 1:
                total_doublings += c - 1

    return stats, total_doublings


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(schedule, sessions):
    session_map = {s["id"]: s for s in sessions}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Time"] + ROOM_NAMES)

        writer.writerow(["07:30am - 08:30am | Breakfast"] + ["Breakfast"] * 8)

        slot_keys = sorted(schedule.keys())
        for i, slot_key in enumerate(slot_keys[:4]):
            row = [SLOT_TIMES[i]]
            for sid in schedule[slot_key]:
                s = session_map.get(str(sid))
                row.append(
                    f"{s['title']} - {s['speakers']}" if s else f"Unknown ({sid})"
                )
            writer.writerow(row)

        writer.writerow(["12:15pm - 01:00pm | Lunch"] + ["Lunch"] * 8)
        writer.writerow(["01:00pm - 01:45pm | Pending"] + ["Pending"] * 8)

        for i, slot_key in enumerate(slot_keys[4:]):
            row = [SLOT_TIMES[4 + i]]
            for sid in schedule[slot_key]:
                s = session_map.get(str(sid))
                row.append(
                    f"{s['title']} - {s['speakers']}" if s else f"Unknown ({sid})"
                )
            writer.writerow(row)

        writer.writerow(
            ["05:00pm - 06:00pm | Movie Trailers"] + ["Movie Trailers"] * 8
        )

    print(f"CSV written to {CSV_PATH}")


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def load_versions():
    """Load all versions from versions.json, or return empty list."""
    if VERSIONS_PATH.exists():
        with open(VERSIONS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_version(schedule, label="", description=""):
    """Append a new version to versions.json and return the version number."""
    from datetime import datetime, timezone

    versions = load_versions()
    next_ver = max((v["version"] for v in versions), default=0) + 1

    versions.append({
        "version": next_ver,
        "label": label or f"Version {next_ver}",
        "description": description or "",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schedule": schedule,
    })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(VERSIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2)

    return next_ver


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

def write_html(sessions):
    """Generate schedule.html from template with all versions and drag-and-drop PR support."""
    versions = load_versions()
    if not versions:
        print("No versions found; skipping HTML generation.", file=sys.stderr)
        return

    # Read HTML template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Build data injections
    sessions_dict = {
        s["id"]: {"title": s["title"], "speakers": s["speakers"], "track": s["track"]}
        for s in sessions
    }
    rooms_list = [
        {"num": r["num"], "alias": r["alias"], "capacity": r["capacity"],
         "live": r["live"], "simulcast": r["simulcast"].replace("Theaters ", "").replace("Theater ", "")}
        for r in ROOMS
    ]

    html = template
    html = html.replace("__ROOMS_DATA__", json.dumps(rooms_list, indent=2))
    html = html.replace("__SESSIONS_DATA__", json.dumps(sessions_dict, indent=2))
    html = html.replace("__VERSIONS_DATA__", json.dumps(versions, indent=2))
    html = html.replace("__ATTENDANCE_DATA__", json.dumps(ATTENDANCE_2025, indent=2))

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML written to {HTML_PATH}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Stir Trek 2026 Schedule Builder")
    parser.add_argument(
        "--prompt", action="store_true",
        help="Print the prompt to stdout and exit (no CLI call)",
    )
    parser.add_argument(
        "--from-json", metavar="FILE",
        help="Skip Claude CLI; read schedule from a JSON file",
    )
    parser.add_argument(
        "--version-label", metavar="LABEL",
        help="Label for this schedule version (default: auto-numbered)",
    )
    parser.add_argument(
        "--version-desc", metavar="DESC",
        help="Description for this schedule version",
    )
    parser.add_argument(
        "--html-only", action="store_true",
        help="Regenerate HTML from existing versions.json (no scheduling)",
    )
    args = parser.parse_args()

    # Load sessions
    print("Loading session data...", file=sys.stderr)
    sessions = load_sessions()
    multi_speakers = find_multi_session_speakers(sessions)
    print(f"  {len(sessions)} sessions, {len(multi_speakers)} multi-session speakers",
          file=sys.stderr)

    # HTML-only mode: regenerate HTML and exit
    if args.html_only:
        write_html(sessions)
        print("Done!", file=sys.stderr)
        return

    tracks = Counter(s["track"] for s in sessions)
    for track, count in tracks.most_common():
        print(f"  {track}: {count}", file=sys.stderr)

    # Build prompt (always needed for --prompt mode, useful to log otherwise)
    prompt = build_prompt(sessions, multi_speakers)

    # --prompt mode: just dump it and exit
    if args.prompt:
        print(prompt)
        return

    # Get schedule: either from file or from Claude CLI
    if args.from_json:
        print(f"Reading schedule from {args.from_json}...", file=sys.stderr)
        with open(args.from_json) as f:
            schedule = json.load(f)
    else:
        schedule = call_claude(prompt)

    # Normalize IDs to strings
    schedule = {
        k: [str(sid) for sid in v] for k, v in schedule.items()
    }

    # Save the raw schedule JSON for reuse
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, "w") as f:
        json.dump(schedule, f, indent=2)
    print(f"Schedule JSON saved to {JSON_PATH}", file=sys.stderr)

    # Validate
    print("\n--- Validation ---", file=sys.stderr)
    ok, errors = validate_schedule(schedule, sessions)
    if ok:
        print("PASS: All hard constraints satisfied", file=sys.stderr)
    else:
        print("FAIL: Constraint violations:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    # Track stats
    print("\n--- Track Distribution ---", file=sys.stderr)
    stats, total_doublings = compute_track_stats(schedule, sessions)
    for slot_name, track_counts in stats.items():
        doubled = {t: c for t, c in track_counts.items() if c > 1}
        suffix = f"  doubled: {dict(doubled)}" if doubled else ""
        print(f"  {slot_name}: {len(track_counts)} unique tracks{suffix}",
              file=sys.stderr)
    print(f"  Total track doublings: {total_doublings}", file=sys.stderr)

    # Save version
    ver = save_version(
        schedule,
        label=args.version_label or "",
        description=args.version_desc or "",
    )
    print(f"Saved as version {ver}", file=sys.stderr)

    # Write CSV + HTML
    write_csv(schedule, sessions)
    write_html(sessions)
    print("\nDone!", file=sys.stderr)


if __name__ == "__main__":
    main()
