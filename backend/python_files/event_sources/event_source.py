from abc import ABC, abstractmethod


class EventSource(ABC):
    name = None
    priority = 0

    def __init__(self, bucket_name, existing_event_ids, days_out):
        self.bucket_name = bucket_name
        self.existing_event_ids = set(existing_event_ids)
        self.days_out = days_out

    @abstractmethod
    def collect(self):
        """Return raw events from this source."""

    @abstractmethod
    def parse(self, event_data, event_fields):
        """Populate and return event_fields, or return None to skip the event."""
