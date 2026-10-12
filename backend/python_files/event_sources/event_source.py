from abc import ABC, abstractmethod
from typing import Any, Iterable

from backend.python_files.event_class import EventDraft


class EventSource(ABC):
    name: str = ""
    priority: int = 0

    def __init__(self, bucket_name, existing_event_ids, days_out):
        self.bucket_name = bucket_name
        self.existing_event_ids = set(existing_event_ids)
        self.days_out = days_out

    @abstractmethod
    def collect(self) -> Iterable[Any]:
        """Return raw events from this source."""

    def new_event_draft(self) -> EventDraft:
        return EventDraft(source=self.name)

    @abstractmethod
    def parse(self, event_data: Any) -> EventDraft | None:
        """Return a normalized event draft, or None to skip the event."""
