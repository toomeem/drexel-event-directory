class Event:
    def __init__(self, event_id, source, name, org_name, location, start_time, end_time, image_url):
        self.event_id = event_id
        self.source = source
        self.name = name
        self.org_name = org_name
        self.location = location
        self.image_url = image_url
        self.start_time = start_time
        self.end_time = end_time

    def __eq__(self, other):
        return self.event_id == other.event_id

    def get_start_timestamp(self):
        return round(self.start_time.timestamp()) if self.start_time else None

    def get_end_timestamp(self):
        return round(self.end_time.timestamp()) if self.end_time else None

    def to_json(self):
        return {
            "event_id": self.event_id,
            "source": self.source,
            "name": self.name,
            "org_name": self.org_name,
            "location": self.location,
            "start_time": self.get_start_timestamp(),
            "end_time": self.get_end_timestamp(),
            "image_url": self.image_url,
        }
