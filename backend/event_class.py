class Event:
    def __init__(self, _id, source, name, org_name, location, image_url, start_time, end_time, event_link, event_status,
                 theme, perks):
        self._id = _id
        self.source = source
        self.name = name
        self.org_name = org_name
        self.location = location
        self.image_url = image_url
        self.start_time = start_time
        self.end_time = end_time
        self.event_link = event_link
        self.event_status = event_status  # 'in-person', 'virtual', 'hybrid'
        self.theme = theme  # academic, arts, athletics, career, community, cultural, fundraising, social, spirituality
        self.perks = perks  # free_food, free_stuff, credit

    def get_start_timestamp(self):
        return round(self.start_time.timestamp()) if self.start_time else None

    def get_end_timestamp(self):
        return round(self.end_time.timestamp()) if self.end_time else None

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        if self.source == other.source and self.source != "drexel_athletics":
            return False
        if self.get_start_timestamp() != other.get_start_timestamp():
            return False
        if self.get_end_timestamp() != other.get_end_timestamp():
            return False
        if self.name.lower().strip() == other.name.lower().strip():
            return True
        return False

    def to_json(self):
        return {"id": self._id, "source": self.source, "name": self.name, "org_name": self.org_name,
                "location": self.location, "image_url": self.image_url, "start_time": self.get_start_timestamp(),
                "end_time": self.get_end_timestamp(), "event_link": self.event_link, "event_status": self.event_status,
                "theme": self.theme, "perks": self.perks, }

    def to_sql(self):
        return (self._id, self.source, self.name, self.org_name, self.location, self.image_url,
                self.get_start_timestamp(), self.get_end_timestamp(), self.event_link, self.event_status, self.theme,
                "|".join(self.perks),)
