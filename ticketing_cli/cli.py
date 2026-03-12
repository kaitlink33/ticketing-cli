"""CLI entry point for ticketing-cli."""

import argparse
import sys
from pathlib import Path

from .display import (
    print_error, print_info, print_success, print_table, ticket_detail
)
from .exporter import export_csv, export_json
from .models import Priority, PriorityQueue, Status, Ticket
from .storage import load_tickets, save_tickets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(store: Path | None = None) -> dict[str, Ticket]:
    return load_tickets(store)


def _save(tickets: dict[str, Ticket], store: Path | None = None):
    save_tickets(tickets, store)


def _get_ticket(tickets: dict[str, Ticket], tid: str) -> Ticket | None:
    tid = tid.upper()
    if tid in tickets:
        return tickets[tid]
    # fuzzy: prefix match
    matches = [t for t in tickets.values() if t.id.startswith(tid)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print_error(f"Ambiguous ID '{tid}': matches {[t.id for t in matches]}")
    else:
        print_error(f"No ticket found with ID '{tid}'")
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_add(args):
    tickets = _load(args.store)
    try:
        priority = Priority.from_string(args.priority)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    ticket = Ticket(
        title=args.title,
        description=args.description or "",
        priority=priority,
        assignee=args.assignee,
        tags=tags,
    )
    tickets[ticket.id] = ticket
    _save(tickets, args.store)
    print_success(f"Ticket created: {ticket.id}  '{ticket.title}'")


def cmd_list(args):
    tickets = _load(args.store)

    filtered = list(tickets.values())

    if args.status:
        try:
            status_filter = Status.from_string(args.status)
        except ValueError as e:
            print_error(str(e))
            sys.exit(1)
        filtered = [t for t in filtered if t.status == status_filter]

    if args.priority:
        try:
            priority_filter = Priority.from_string(args.priority)
        except ValueError as e:
            print_error(str(e))
            sys.exit(1)
        filtered = [t for t in filtered if t.priority == priority_filter]

    if args.assignee:
        filtered = [t for t in filtered if t.assignee == args.assignee]

    if args.tag:
        filtered = [t for t in filtered if args.tag in t.tags]

    # Sort via priority queue
    pq = PriorityQueue()
    pq.rebuild(filtered)
    sorted_tickets = list(pq)

    print_info(f"{len(sorted_tickets)} ticket(s) found")
    print_table(sorted_tickets)


def cmd_show(args):
    tickets = _load(args.store)
    ticket = _get_ticket(tickets, args.id)
    if ticket:
        ticket_detail(ticket)


def cmd_update(args):
    tickets = _load(args.store)
    ticket = _get_ticket(tickets, args.id)
    if not ticket:
        sys.exit(1)

    changed = []

    if args.status:
        try:
            ticket.status = Status.from_string(args.status)
            changed.append(f"status -> {ticket.status.label()}")
        except ValueError as e:
            print_error(str(e))
            sys.exit(1)

    if args.priority:
        try:
            ticket.priority = Priority.from_string(args.priority)
            changed.append(f"priority -> {ticket.priority.label()}")
        except ValueError as e:
            print_error(str(e))
            sys.exit(1)

    if args.assignee is not None:
        ticket.assignee = args.assignee or None
        changed.append(f"assignee -> {ticket.assignee or '(unassigned)'}")

    if args.title:
        ticket.title = args.title
        changed.append(f"title -> {ticket.title}")

    if args.description:
        ticket.description = args.description
        changed.append("description updated")

    if args.add_tag:
        for tag in args.add_tag.split(","):
            tag = tag.strip()
            if tag and tag not in ticket.tags:
                ticket.tags.append(tag)
        changed.append(f"tags -> {ticket.tags}")

    if args.remove_tag:
        ticket.tags = [t for t in ticket.tags if t != args.remove_tag.strip()]
        changed.append(f"tags -> {ticket.tags}")

    if not changed:
        print_info("Nothing to update.")
        return

    ticket.touch()
    _save(tickets, args.store)
    for c in changed:
        print_success(f"{ticket.id}: {c}")


def cmd_note(args):
    tickets = _load(args.store)
    ticket = _get_ticket(tickets, args.id)
    if not ticket:
        sys.exit(1)
    ticket.add_note(args.text, author=args.author or "user")
    _save(tickets, args.store)
    print_success(f"Note added to {ticket.id}")


def cmd_close(args):
    tickets = _load(args.store)
    ticket = _get_ticket(tickets, args.id)
    if not ticket:
        sys.exit(1)
    ticket.status = Status.CLOSED
    ticket.touch()
    _save(tickets, args.store)
    print_success(f"Ticket {ticket.id} closed.")


def cmd_delete(args):
    tickets = _load(args.store)
    ticket = _get_ticket(tickets, args.id)
    if not ticket:
        sys.exit(1)
    if not args.force:
        confirm = input(f"Delete ticket {ticket.id} '{ticket.title}'? [y/N]: ")
        if confirm.strip().lower() != "y":
            print_info("Aborted.")
            return
    del tickets[ticket.id]
    _save(tickets, args.store)
    print_success(f"Ticket {ticket.id} deleted.")


def cmd_export(args):
    tickets = _load(args.store)
    dest = Path(args.output)
    fmt = args.format.lower()

    all_tickets = list(tickets.values())

    if fmt == "json":
        export_json(all_tickets, dest)
    elif fmt == "csv":
        export_csv(all_tickets, dest)
    else:
        print_error(f"Unknown format '{fmt}'. Use 'json' or 'csv'.")
        sys.exit(1)

    print_success(f"Exported {len(all_tickets)} ticket(s) to {dest}")


def cmd_next(args):
    tickets = _load(args.store)
    open_tickets = [
        t for t in tickets.values()
        if t.status in (Status.OPEN, Status.IN_PROGRESS)
    ]
    pq = PriorityQueue()
    pq.rebuild(open_tickets)
    top = pq.peek()
    if top:
        print_info("Next ticket to work on:")
        ticket_detail(top)
    else:
        print_info("No open tickets in the queue.")


def cmd_stats(args):
    tickets = _load(args.store)
    total = len(tickets)
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    for t in tickets.values():
        by_status[t.status.label()] = by_status.get(t.status.label(), 0) + 1
        by_priority[t.priority.label()] = by_priority.get(t.priority.label(), 0) + 1

    print(f"\n  Total tickets: {total}\n")
    print("  By status:")
    for k, v in sorted(by_status.items()):
        print(f"    {k:<14} {v}")
    print("  By priority:")
    for k, v in sorted(by_priority.items()):
        print(f"    {k:<14} {v}")
    print()


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tkt",
        description="ticketing-cli: priority-queue-driven ticket management from the terminal",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=None,
        help="Path to the JSON store file (default: ~/.ticketing-cli/tickets.json)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Create a new ticket")
    p_add.add_argument("title", help="Short title for the ticket")
    p_add.add_argument("-d", "--description", help="Detailed description")
    p_add.add_argument(
        "-p", "--priority",
        default="medium",
        help="Priority: low, medium, high, critical (default: medium)",
    )
    p_add.add_argument("-a", "--assignee", help="Assignee name or handle")
    p_add.add_argument("-t", "--tags", help="Comma-separated tags")

    # list
    p_list = sub.add_parser("list", help="List tickets with optional filters")
    p_list.add_argument("-s", "--status", help="Filter by status")
    p_list.add_argument("-p", "--priority", help="Filter by priority")
    p_list.add_argument("-a", "--assignee", help="Filter by assignee")
    p_list.add_argument("--tag", help="Filter by tag")

    # show
    p_show = sub.add_parser("show", help="Show full details for a ticket")
    p_show.add_argument("id", help="Ticket ID")

    # update
    p_update = sub.add_parser("update", help="Update ticket fields")
    p_update.add_argument("id", help="Ticket ID")
    p_update.add_argument("-s", "--status", help="New status")
    p_update.add_argument("-p", "--priority", help="New priority")
    p_update.add_argument("-a", "--assignee", help="New assignee (empty string to unassign)")
    p_update.add_argument("--title", help="New title")
    p_update.add_argument("-d", "--description", help="New description")
    p_update.add_argument("--add-tag", help="Add a tag (comma-separated)")
    p_update.add_argument("--remove-tag", help="Remove a tag")

    # note
    p_note = sub.add_parser("note", help="Add a note to a ticket")
    p_note.add_argument("id", help="Ticket ID")
    p_note.add_argument("text", help="Note text")
    p_note.add_argument("--author", help="Author name (default: user)")

    # close
    p_close = sub.add_parser("close", help="Mark a ticket as closed")
    p_close.add_argument("id", help="Ticket ID")

    # delete
    p_delete = sub.add_parser("delete", help="Permanently delete a ticket")
    p_delete.add_argument("id", help="Ticket ID")
    p_delete.add_argument("-f", "--force", action="store_true", help="Skip confirmation")

    # export
    p_export = sub.add_parser("export", help="Export all tickets to JSON or CSV")
    p_export.add_argument("output", help="Destination file path")
    p_export.add_argument(
        "-f", "--format",
        default="json",
        help="Export format: json or csv (default: json)",
    )

    # next
    sub.add_parser("next", help="Show the highest-priority open ticket")

    # stats
    sub.add_parser("stats", help="Print summary statistics")

    return parser


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "add": cmd_add,
    "list": cmd_list,
    "show": cmd_show,
    "update": cmd_update,
    "note": cmd_note,
    "close": cmd_close,
    "delete": cmd_delete,
    "export": cmd_export,
    "next": cmd_next,
    "stats": cmd_stats,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    fn = COMMAND_MAP.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
