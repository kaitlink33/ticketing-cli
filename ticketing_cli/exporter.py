"""Export tickets to JSON or CSV."""

import csv
import json
from pathlib import Path
from typing import Optional

from .models import Ticket


def export_json(tickets: list[Ticket], dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in tickets], f, indent=2)


def export_csv(tickets: list[Ticket], dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id", "title", "description", "priority", "status",
        "assignee", "tags", "created_at", "updated_at",
    ]
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ticket in tickets:
            row = ticket.to_dict()
            row["tags"] = "; ".join(row.get("tags") or [])
            row.pop("notes", None)
            writer.writerow({k: row.get(k, "") for k in fieldnames})
