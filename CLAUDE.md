# Project: Stir Trek 2026 Schedule Builder

## What This Is
Conference schedule optimizer for Stir Trek 2026. Assigns 56 sessions across 7 time slots × 8 rooms using Claude CLI, then serves an interactive HTML schedule on GitHub Pages with drag-and-drop exploration.

## Quick Reference

### Key Commands
```bash
python schedule_builder.py --html-only    # Regenerate HTML from versions.json
python schedule_builder.py --from-json output/schedule.json  # Re-import a schedule
python schedule_builder.py --prompt       # Print the Claude prompt
```

### Key Files
- `schedule_builder.py` — main script, all logic lives here
- `templates/schedule_template.html` — HTML template with `__PLACEHOLDER__` tokens
- `output/versions.json` — all schedule versions (don't edit by hand)
- `data/speaker_preferences.md` — speaker scheduling preferences (fed into Claude prompt)

## Development Notes

### After modifying .py files
Always run or offer to run: `python schedule_builder.py --html-only` to verify nothing broke.

### After modifying the HTML template
Run `python schedule_builder.py --html-only` to regenerate `output/schedule.html`.

### Template placeholders
`__ROOMS_DATA__`, `__SESSIONS_DATA__`, `__VERSIONS_DATA__`, `__ATTENDANCE_DATA__` — all replaced by `write_html()` in schedule_builder.py.

### Version management
- Every `--from-json` run appends a version to `versions.json`
- Be careful not to run it multiple times with the same data (creates duplicates)
- `--html-only` does NOT create a new version

### Speaker preferences
- Edit `data/speaker_preferences.md` to add/change speaker constraints
- Preferences are included verbatim in the Claude prompt
- Supports room sizing, time slot preferences, unavailable slots, and scheduling conflicts

### Room array positions matter
Array index in schedule JSON = room assignment. Position 0 = Room 1 (388 seats), Position 7 = Room 8 (173 seats). Don't reorder ROOMS list without updating everything downstream.
