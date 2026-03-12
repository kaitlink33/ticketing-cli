"""Persistence layer: load and save ticket data as JSON."""

import json
import os
from pathlib import Path
from typing import Optional

from .models import Ticket

DEFAULT_STORE = Path.home() / ".ticketing-cli" / "tickets.json"


def _resolve_store(path: Optional[Path] = None) -> Path:
    store = path or Path(os.environ.get("TICKETING_STORE", str(DEFAULT_STORE)))
    store.parent.mkdir(parents=True, exist_ok=True)
    return store


def load_tickets(path: Optional[Path] = None) -> dict[str, Ticket]:
    store = _resolve_store(path)
    if not store.exists():
        return {}
    with open(store, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {tid: Ticket.from_dict(data) for tid, data in raw.items()}


def save_tickets(tickets: dict[str, Ticket], path: Optional[Path] = None):
    store = _resolve_store(path)
    with open(store, "w", encoding="utf-8") as f:
        json.dump({tid: t.to_dict() for tid, t in tickets.items()}, f, indent=2)
