#!/usr/bin/env python3
"""
Extract and validate a schedule swap proposal from a GitHub Issue body.

Reads the issue body from the ISSUE_BODY environment variable,
extracts the proposed schedule JSON, validates it, and writes it
to output/schedule.json for further processing by schedule_builder.py.
"""

import json
import os
import re
import sys

# Add project root to path so we can import schedule_builder
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
from schedule_builder import load_sessions, validate_schedule


def extract_schedule(body):
    """Extract proposed schedule JSON from the issue body."""
    if "<!-- SCHEDULE_SWAP -->" not in body:
        print("No SCHEDULE_SWAP marker found in issue body", file=sys.stderr)
        sys.exit(1)

    # Look for JSON code fence after "Proposed Schedule" heading
    match = re.search(
        r"### Proposed Schedule\s*```json\s*(\{.*?\})\s*```",
        body,
        re.DOTALL,
    )
    if not match:
        # Fallback: any JSON code fence containing slot_1
        match = re.search(
            r'```json\s*(\{[^`]*"slot_1"[^`]*\})\s*```',
            body,
            re.DOTALL,
        )

    if not match:
        print("Could not find schedule JSON in issue body", file=sys.stderr)
        sys.exit(1)

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in schedule: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    body = os.environ.get("ISSUE_BODY", "")
    issue_num = os.environ.get("ISSUE_NUMBER", "?")

    if not body:
        print("ISSUE_BODY environment variable is empty", file=sys.stderr)
        sys.exit(1)

    print(f"Processing schedule swap from issue #{issue_num}...")

    # Extract schedule
    schedule = extract_schedule(body)

    # Normalize IDs to strings
    schedule = {k: [str(sid) for sid in v] for k, v in schedule.items()}

    # Validate against session data
    sessions = load_sessions()
    ok, errors = validate_schedule(schedule, sessions)

    if not ok:
        print("Validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print("Validation passed")

    # Write to output/schedule.json
    os.makedirs("output", exist_ok=True)
    with open("output/schedule.json", "w") as f:
        json.dump(schedule, f, indent=2)

    print("Schedule written to output/schedule.json")


if __name__ == "__main__":
    main()
