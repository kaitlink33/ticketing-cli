"""Core data models for the ticketing system."""

import uuid
import heapq
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_string(cls, value: str) -> "Priority":
        mapping = {
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        key = value.strip().lower()
        if key not in mapping:
            raise ValueError(
                f"Invalid priority '{value}'. Choose from: low, medium, high, critical"
            )
        return mapping[key]

    def label(self) -> str:
        return self.name.capitalize()


class Status(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

    @classmethod
    def from_string(cls, value: str) -> "Status":
        mapping = {
            "open": cls.OPEN,
            "in_progress": cls.IN_PROGRESS,
            "in progress": cls.IN_PROGRESS,
            "resolved": cls.RESOLVED,
            "closed": cls.CLOSED,
        }
        key = value.strip().lower()
        if key not in mapping:
            raise ValueError(
                f"Invalid status '{value}'. Choose from: open, in_progress, resolved, closed"
            )
        return mapping[key]

    def label(self) -> str:
        return self.value.replace("_", " ").title()


@dataclass
class Ticket:
    title: str
    description: str
    priority: Priority
    assignee: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    status: Status = field(default=Status.OPEN)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.name,
            "status": self.status.value,
            "assignee": self.assignee,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        ticket = cls(
            title=data["title"],
            description=data["description"],
            priority=Priority[data["priority"]],
            assignee=data.get("assignee"),
            tags=data.get("tags", []),
            id=data["id"],
            status=Status(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
        ticket.notes = data.get("notes", [])
        return ticket

    def touch(self):
        self.updated_at = datetime.utcnow().isoformat()

    def add_note(self, text: str, author: str = "system"):
        self.notes.append({
            "author": author,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.touch()

    # Priority queue comparison: higher priority and older tickets come first
    def __lt__(self, other: "Ticket") -> bool:
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class PriorityQueue:
    """Min-heap based priority queue that surfaces highest-priority tickets first."""

    def __init__(self):
        self._heap: list[Ticket] = []

    def push(self, ticket: Ticket):
        heapq.heappush(self._heap, ticket)

    def pop(self) -> Optional[Ticket]:
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self) -> Optional[Ticket]:
        if self._heap:
            return self._heap[0]
        return None

    def rebuild(self, tickets: list[Ticket]):
        self._heap = list(tickets)
        heapq.heapify(self._heap)

    def __len__(self) -> int:
        return len(self._heap)

    def __iter__(self):
        return iter(sorted(self._heap))
