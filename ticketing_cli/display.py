"""Terminal display helpers."""

from .models import Priority, Status, Ticket

PRIORITY_COLORS = {
    Priority.LOW: "\033[36m",      # cyan
    Priority.MEDIUM: "\033[33m",   # yellow
    Priority.HIGH: "\033[31m",     # red
    Priority.CRITICAL: "\033[35m", # magenta
}

STATUS_COLORS = {
    Status.OPEN: "\033[32m",          # green
    Status.IN_PROGRESS: "\033[33m",   # yellow
    Status.RESOLVED: "\033[34m",      # blue
    Status.CLOSED: "\033[90m",        # dark gray
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def colorize(text: str, code: str) -> str:
    return f"{code}{text}{RESET}"


def priority_badge(priority: Priority) -> str:
    color = PRIORITY_COLORS.get(priority, "")
    return colorize(f"[{priority.label()}]", color)


def status_badge(status: Status) -> str:
    color = STATUS_COLORS.get(status, "")
    return colorize(f"[{status.label()}]", color)


def ticket_row(ticket: Ticket) -> str:
    parts = [
        colorize(ticket.id, BOLD),
        status_badge(ticket.status),
        priority_badge(ticket.priority),
        ticket.title,
    ]
    if ticket.assignee:
        parts.append(colorize(f"@{ticket.assignee}", DIM))
    return "  ".join(parts)


def ticket_detail(ticket: Ticket):
    sep = "-" * 60
    print(sep)
    print(f"{BOLD}ID:{RESET}          {ticket.id}")
    print(f"{BOLD}Title:{RESET}       {ticket.title}")
    print(f"{BOLD}Status:{RESET}      {status_badge(ticket.status)}")
    print(f"{BOLD}Priority:{RESET}    {priority_badge(ticket.priority)}")
    print(f"{BOLD}Assignee:{RESET}    {ticket.assignee or '(unassigned)'}")
    print(f"{BOLD}Tags:{RESET}        {', '.join(ticket.tags) if ticket.tags else '(none)'}")
    print(f"{BOLD}Created:{RESET}     {ticket.created_at}")
    print(f"{BOLD}Updated:{RESET}     {ticket.updated_at}")
    print(f"{BOLD}Description:{RESET}")
    for line in ticket.description.splitlines():
        print(f"  {line}")
    if ticket.notes:
        print(f"\n{BOLD}Notes:{RESET}")
        for note in ticket.notes:
            print(f"  [{note['timestamp']}] {note['author']}: {note['text']}")
    print(sep)


def print_table(tickets: list[Ticket]):
    if not tickets:
        print("  No tickets found.")
        return
    for t in tickets:
        print(ticket_row(t))


def print_success(msg: str):
    print(colorize(f"OK  {msg}", "\033[32m"))


def print_error(msg: str):
    print(colorize(f"ERR {msg}", "\033[31m"))


def print_info(msg: str):
    print(colorize(f"... {msg}", "\033[36m"))
