"""Tests for ticketing-cli core logic."""

import json
import csv
import tempfile
from pathlib import Path

import pytest

from ticketing_cli.models import Priority, PriorityQueue, Status, Ticket
from ticketing_cli.storage import load_tickets, save_tickets
from ticketing_cli.exporter import export_json, export_csv


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestPriority:
    def test_from_string_valid(self):
        assert Priority.from_string("high") == Priority.HIGH
        assert Priority.from_string("CRITICAL") == Priority.CRITICAL
        assert Priority.from_string("  low  ") == Priority.LOW

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Priority.from_string("urgent")

    def test_label(self):
        assert Priority.MEDIUM.label() == "Medium"


class TestStatus:
    def test_from_string_valid(self):
        assert Status.from_string("open") == Status.OPEN
        assert Status.from_string("in_progress") == Status.IN_PROGRESS
        assert Status.from_string("in progress") == Status.IN_PROGRESS

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Status.from_string("pending")


class TestTicket:
    def test_creation_defaults(self):
        t = Ticket(title="Bug fix", description="Broken login", priority=Priority.HIGH)
        assert t.status == Status.OPEN
        assert len(t.id) == 8
        assert t.notes == []

    def test_to_dict_roundtrip(self):
        t = Ticket(
            title="Feature",
            description="Add dark mode",
            priority=Priority.LOW,
            assignee="alice",
            tags=["ui", "enhancement"],
        )
        d = t.to_dict()
        restored = Ticket.from_dict(d)
        assert restored.id == t.id
        assert restored.title == t.title
        assert restored.priority == t.priority
        assert restored.status == t.status
        assert restored.tags == t.tags

    def test_add_note(self):
        t = Ticket(title="Test", description="", priority=Priority.MEDIUM)
        t.add_note("First note", author="dev")
        assert len(t.notes) == 1
        assert t.notes[0]["author"] == "dev"
        assert t.notes[0]["text"] == "First note"

    def test_touch_updates_timestamp(self):
        t = Ticket(title="t", description="", priority=Priority.LOW)
        old = t.updated_at
        import time; time.sleep(0.01)
        t.touch()
        assert t.updated_at >= old


# ---------------------------------------------------------------------------
# Priority queue tests
# ---------------------------------------------------------------------------

class TestPriorityQueue:
    def test_ordering(self):
        pq = PriorityQueue()
        low = Ticket(title="Low", description="", priority=Priority.LOW)
        high = Ticket(title="High", description="", priority=Priority.HIGH)
        critical = Ticket(title="Critical", description="", priority=Priority.CRITICAL)
        for t in [low, high, critical]:
            pq.push(t)
        assert pq.pop().priority == Priority.CRITICAL
        assert pq.pop().priority == Priority.HIGH
        assert pq.pop().priority == Priority.LOW

    def test_peek_does_not_pop(self):
        pq = PriorityQueue()
        t = Ticket(title="T", description="", priority=Priority.HIGH)
        pq.push(t)
        assert pq.peek() is not None
        assert len(pq) == 1

    def test_empty_queue(self):
        pq = PriorityQueue()
        assert pq.pop() is None
        assert pq.peek() is None

    def test_rebuild(self):
        pq = PriorityQueue()
        tickets = [
            Ticket(title="a", description="", priority=Priority.LOW),
            Ticket(title="b", description="", priority=Priority.CRITICAL),
        ]
        pq.rebuild(tickets)
        assert len(pq) == 2
        assert pq.peek().priority == Priority.CRITICAL


# ---------------------------------------------------------------------------
# Storage tests
# ---------------------------------------------------------------------------

class TestStorage:
    def test_save_and_load(self, tmp_path):
        store = tmp_path / "tickets.json"
        t = Ticket(title="Save me", description="desc", priority=Priority.MEDIUM)
        save_tickets({t.id: t}, store)
        loaded = load_tickets(store)
        assert t.id in loaded
        assert loaded[t.id].title == "Save me"

    def test_load_missing_file(self, tmp_path):
        store = tmp_path / "nonexistent.json"
        result = load_tickets(store)
        assert result == {}

    def test_multiple_tickets(self, tmp_path):
        store = tmp_path / "tickets.json"
        tickets = {
            t.id: t for t in [
                Ticket(title="A", description="", priority=Priority.LOW),
                Ticket(title="B", description="", priority=Priority.HIGH),
                Ticket(title="C", description="", priority=Priority.CRITICAL),
            ]
        }
        save_tickets(tickets, store)
        loaded = load_tickets(store)
        assert len(loaded) == 3


# ---------------------------------------------------------------------------
# Exporter tests
# ---------------------------------------------------------------------------

class TestExporter:
    def _sample_tickets(self):
        return [
            Ticket(title="Alpha", description="First", priority=Priority.HIGH, tags=["backend"]),
            Ticket(title="Beta", description="Second", priority=Priority.LOW, assignee="bob"),
        ]

    def test_export_json(self, tmp_path):
        dest = tmp_path / "out.json"
        tickets = self._sample_tickets()
        export_json(tickets, dest)
        data = json.loads(dest.read_text())
        assert len(data) == 2
        assert data[0]["title"] == "Alpha"
        assert data[1]["assignee"] == "bob"

    def test_export_csv(self, tmp_path):
        dest = tmp_path / "out.csv"
        tickets = self._sample_tickets()
        export_csv(tickets, dest)
        with open(dest, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["title"] == "Alpha"
        assert rows[0]["tags"] == "backend"
        assert rows[1]["assignee"] == "bob"

    def test_export_json_creates_parent_dirs(self, tmp_path):
        dest = tmp_path / "nested" / "dir" / "out.json"
        export_json(self._sample_tickets(), dest)
        assert dest.exists()
