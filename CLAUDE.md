# Project: Stir Trek 2026 Schedule Builder

## What This Is
Conference schedule optimizer for Stir Trek 2026. Assigns 56 sessions across 7 time slots × 8 rooms using Claude CLI, then serves an interactive HTML schedule on GitHub Pages with drag-and-drop swap proposals.

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
- `.github/workflows/process-swap.yml` — swap proposal automation
- `.github/scripts/process_swap.py` — extracts + validates swaps from GitHub Issues

### How the Swap Flow Works
1. User drags sessions in HTML → clicks "Propose Changes"
2. Pre-filled GitHub Issue opens with `<!-- SCHEDULE_SWAP -->` marker + schedule JSON
3. GitHub Action validates the schedule and creates a PR
4. `process_swap.py` generates `output/pr_body.md` with detailed diff table
5. PR includes updated schedule.json, versions.json, schedule.csv, schedule.html

## Development Notes

### After modifying .py files
Always run or offer to run: `python schedule_builder.py --html-only` to verify nothing broke.

### After modifying the HTML template
Run `python schedule_builder.py --html-only` to regenerate `output/schedule.html`.

### Template placeholders
`__ROOMS_DATA__`, `__SESSIONS_DATA__`, `__VERSIONS_DATA__`, `__ATTENDANCE_DATA__`, `__GITHUB_REPO__` — all replaced by `write_html()` in schedule_builder.py.

### Version management
- Every `--from-json` run appends a version to `versions.json`
- Be careful not to run it multiple times with the same data (creates duplicates)
- `--html-only` does NOT create a new version

### GitHub Actions requirements
- Repo setting needed: **Actions > General > Allow GitHub Actions to create and approve pull requests**
- `process_swap.py` imports from `schedule_builder.py` (needs openpyxl installed)
- `output/pr_body.md` is a temp file (gitignored), used to pass rich PR body from Python to the workflow

### Room array positions matter
Array index in schedule JSON = room assignment. Position 0 = Room 1 (388 seats), Position 7 = Room 8 (173 seats). Don't reorder ROOMS list without updating everything downstream.
