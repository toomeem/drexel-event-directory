from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True, eq=False)
class Event:
    _id: str
    source: str
    name: str
    org_name: str
    location: str | None
    image_url: str | None
    start_time: datetime
    end_time: datetime | None
    event_link: str | None
    event_status: str | None
    theme: str | None
    perks: list[str] | None
    food_related: bool
    popular: bool
    recurring: bool
    for_new_students: bool
    on_campus: bool
    religion: str | None

    def get_end_timestamp(self):
        return round(self.end_time.timestamp()) if self.end_time else None

    @classmethod
    def from_json(cls, event_json):
        return cls(
            _id=event_json["id"],
            source=event_json["source"],
            name=event_json["name"],
            org_name=event_json["org_name"],
            location=event_json["location"],
            image_url=event_json["image_url"],
            start_time=datetime.fromtimestamp(event_json["start_time"]) if event_json["start_time"] else None,
            end_time=datetime.fromtimestamp(event_json["end_time"]) if event_json["end_time"] else None,
            event_link=event_json["event_link"],
            event_status=event_json["event_status"],
            theme=event_json["theme"],
            perks=event_json["perks"],
            food_related=event_json["food_related"],
            popular=event_json["popular"],
            recurring=event_json["recurring"],
            for_new_students=event_json["for_new_students"],
            on_campus=event_json["on_campus"],
            religion=event_json["religion"],
        )

    @classmethod
    def from_db_row(cls, row):
        # start_time is stored as UTC without a timezone, so pg8000 returns a naive datetime.
        start_time = row[4].replace(tzinfo=timezone.utc)
        return cls(
            _id=row[0],
            source=row[2],
            name=row[1],
            org_name=row[3],
            start_time=start_time,
            location=None,
            end_time=None,
            image_url=None,
            event_link=None,
            event_status=None,
            theme=None,
            perks=None,
            food_related=False,
            popular=False,
            recurring=False,
            for_new_students=False,
            on_campus=True,
            religion=None,
        )

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        same_start = self.start_time.timestamp() == other.start_time.timestamp()
        same_end = self.end_time is not None and self.get_end_timestamp() == other.get_end_timestamp()
        if self.source == other.source and self.source != "drexel_athletics":
            return self.org_name == other.org_name and (same_start or same_end)
        # only filter out events by the start time because duplicates can have different end times
        if not same_start and not same_end:
            return False
        if self.name.lower().strip() == other.name.lower().strip():
            return True
        if self.org_name.lower().strip() == other.org_name.lower().strip():
            return True
        return False

    def __str__(self):
        return f"Event(id={self._id}, source={self.source}, name={self.name}, org_name={self.org_name}, location={self.location}, image_url={self.image_url}, start_time={self.start_time}, end_time={self.end_time}, event_link={self.event_link}, event_status={self.event_status}, theme={self.theme}, perks={self.perks}, food_related={self.food_related}, popular={self.popular}, recurring={self.recurring}, for_new_students={self.for_new_students}, on_campus={self.on_campus}, religion={self.religion})"

    def to_json(self):
        return {"id": self._id, "source": self.source, "name": self.name, "org_name": self.org_name,
                "location": self.location, "image_url": self.image_url, "start_time": self.start_time.timestamp(),
                "end_time": self.get_end_timestamp(), "event_link": self.event_link, "event_status": self.event_status,
                "theme": self.theme, "perks": self.perks, "food_related": self.food_related, "popular": self.popular,
                "recurring": self.recurring, "for_new_students": self.for_new_students, "on_campus": self.on_campus,
                "religion": self.religion}

    def to_chunk_json(self):
        # Imported here to avoid making the core Event model depend on the API's database package at import time.
        from backend.python_files.lambda_function import is_date_only, make_time_str

        event_json = self.to_json()
        event_json["formatted_time_str"] = make_time_str(
            self.start_time, self.end_time, is_date_only(self.source, self.start_time))
        for key in ("event_link", "image_url", "id", "start_time", "end_time"):
            del event_json[key]
        return event_json

    def to_sql(self):
        return (self._id, self.source, self.name, self.org_name, self.location, self.image_url,
                self.start_time.timestamp(), self.get_end_timestamp(), self.event_link, self.event_status, self.theme,
                "|".join(self.perks), self.food_related, self.popular, self.recurring, self.for_new_students,
                self.on_campus, self.religion)

    def is_out_of_range(self, max_days_out):
        try:
            now = datetime.now(tz=self.start_time.tzinfo)
            if self.end_time:
                if self.end_time < now:
                    return True
            elif self.start_time.date() < now.date():
                return True
            return (self.start_time - now).days > max_days_out
        except Exception:
            print(f"Error checking date range for event {self._id}: {self.start_time}")
            return False


@dataclass(slots=True)
class EventDraft:
    source: str
    _id: str | None = None
    name: str | None = None
    org_name: str | None = None
    location: str | None = None
    image_url: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    event_link: str | None = None
    event_status: str | None = None
    theme: str | None = None
    perks: list[str] = field(default_factory=list)
    food_related: bool = False
    popular: bool = False
    recurring: bool = False
    for_new_students: bool = False
    on_campus: bool = True
    religion: str | None = None
    description: str = ""

    def to_event(self) -> Event:
        if self._id is None or self.name is None or self.start_time is None:
            raise ValueError("event draft is missing required fields")
        return Event(
            _id=self._id,
            source=self.source,
            name=self.name,
            org_name=self.org_name or "",
            location=self.location,
            image_url=self.image_url,
            start_time=self.start_time,
            end_time=self.end_time,
            event_link=self.event_link,
            event_status=self.event_status,
            theme=self.theme,
            perks=self.perks,
            food_related=self.food_related,
            popular=self.popular,
            recurring=self.recurring,
            for_new_students=self.for_new_students,
            on_campus=self.on_campus,
            religion=self.religion,
        )
