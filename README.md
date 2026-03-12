# ticketing-cli

A command-line ticketing system built in pure Python. Create and manage tickets from the terminal with priority-queue-based sorting, status tracking, note history, and structured export to JSON or CSV.

No database required. Tickets are stored in a single JSON file and sorted at runtime using a min-heap so the highest-priority work always surfaces first.

---

## Features

- Priority queue ordering: CRITICAL > HIGH > MEDIUM > LOW, with age-based tiebreaking
- Status lifecycle: open -> in_progress -> resolved -> closed
- Assignee and tag support with filter flags on list
- Per-ticket note history with author and timestamp
- Export to JSON or CSV for use in spreadsheets, dashboards, or other tooling
- Single-file JSON store at `~/.ticketing-cli/tickets.json` (overridable via flag or env var)
- Zero external dependencies

---

## Installation

Requires Python 3.10 or later.

```bash
git clone https://github.com/your-username/ticketing-cli.git
cd ticketing-cli
pip install -e .
```

After installation the `tkt` command is available in your shell.

---

## Quick Start

```bash
# Create a ticket
tkt add "Login page crashes on mobile" -p critical -d "Reproducible on iOS Safari 17" -a alice --tags bug,auth

# List all tickets (sorted by priority)
tkt list

# Filter by status or priority
tkt list --status open --priority high

# View full detail for a ticket
tkt show A1B2C3D4

# Update status or reassign
tkt update A1B2C3D4 --status in_progress --assignee bob

# Add a note
tkt note A1B2C3D4 "Traced to a null pointer in the session handler" --author alice

# See what to work on next
tkt next

# Export everything
tkt export tickets.json
tkt export tickets.csv --format csv

# Summary statistics
tkt stats
```

---

## Commands

| Command | Description |
|---|---|
| `add` | Create a new ticket |
| `list` | List tickets with optional filters |
| `show` | Display full details for a ticket |
| `update` | Modify fields on an existing ticket |
| `note` | Append a note to a ticket |
| `close` | Mark a ticket as closed |
| `delete` | Permanently delete a ticket |
| `export` | Export all tickets to JSON or CSV |
| `next` | Show the highest-priority open ticket |
| `stats` | Print status and priority breakdowns |

---

## `add`

```
tkt add <title> [options]

Options:
  -d, --description TEXT   Detailed description
  -p, --priority LEVEL     low | medium | high | critical  (default: medium)
  -a, --assignee NAME      Assignee handle or name
  -t, --tags LIST          Comma-separated tags
```

---

## `list`

```
tkt list [options]

Options:
  -s, --status STATUS      Filter by status
  -p, --priority LEVEL     Filter by priority
  -a, --assignee NAME      Filter by assignee
  --tag TAG                Filter by a single tag
```

Results are sorted by the priority queue: CRITICAL tickets appear first, oldest tickets break ties within the same priority level.

---

## `update`

```
tkt update <id> [options]

Options:
  -s, --status STATUS      New status
  -p, --priority LEVEL     New priority
  -a, --assignee NAME      New assignee (pass empty string to unassign)
  --title TEXT             New title
  -d, --description TEXT   New description
  --add-tag LIST           Add tags (comma-separated)
  --remove-tag TAG         Remove a single tag
```

---

## `export`

```
tkt export <output-path> [--format json|csv]
```

JSON output is a list of ticket objects. CSV output contains one row per ticket; multi-value fields like `tags` are joined with `; `. The `notes` field is omitted from CSV exports.

Example JSON record:

```json
{
  "id": "A1B2C3D4",
  "title": "Login page crashes on mobile",
  "description": "Reproducible on iOS Safari 17",
  "priority": "CRITICAL",
  "status": "in_progress",
  "assignee": "alice",
  "tags": ["bug", "auth"],
  "created_at": "2024-11-01T14:22:00.000000",
  "updated_at": "2024-11-02T09:05:11.000000",
  "notes": [
    {
      "author": "alice",
      "text": "Traced to a null pointer in the session handler",
      "timestamp": "2024-11-02T09:05:11.000000"
    }
  ]
}
```

---

## Configuration

The store path can be set in three ways, in order of precedence:

1. The `--store` flag on any command
2. The `TICKETING_STORE` environment variable
3. Default: `~/.ticketing-cli/tickets.json`

```bash
# Use a project-local store
TICKETING_STORE=./project-tickets.json tkt list

# Or with the flag
tkt --store ./project-tickets.json add "New ticket"
```

---

## Priority Queue Internals

Tickets are ordered using a min-heap (`heapq`) with a custom comparator:

1. Higher numeric priority value comes first (CRITICAL=4 > HIGH=3 > MEDIUM=2 > LOW=1)
2. Within the same priority level, older tickets (earlier `created_at`) come first

This means `tkt next` and sorted `tkt list` output always reflect the ticket that has been waiting the longest at the highest urgency, without any manual ranking.

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Project Structure

```
ticketing-cli/
  ticketing_cli/
    __init__.py      Package metadata
    models.py        Ticket, Priority, Status, PriorityQueue
    storage.py       JSON persistence
    exporter.py      JSON and CSV export
    display.py       Terminal color output
    cli.py           Argparse commands and dispatch
  tests/
    test_core.py     Unit tests for models, storage, and export
  pyproject.toml
  README.md
  LICENSE
```
## Data Dump 
ticketing_cli/models.py is the core: a Ticket dataclass, Priority and Status enums, and a PriorityQueue backed by heapq. The comparator puts CRITICAL tickets first and breaks ties by age, so tkt next always gives you the most urgent thing that has been waiting the longest.
ticketing_cli/cli.py wires ten subcommands through argparse: add, list, show, update, note, close, delete, export, next, and stats. The store path can be overridden per-command with --store or globally with the TICKETING_STORE env var.
ticketing_cli/exporter.py handles both formats. JSON is a clean list of objects. CSV flattens multi-value fields and drops notes since that data does not map well to columns.
ticketing_cli/display.py uses ANSI codes for colored priority and status badges in the terminal, with no external dependencies.
tests/test_core.py covers models, the priority queue, storage roundtrips, and both export formats with pytest (install separately with pip install pytest).

---

## License

MIT
