class Event:
    def __init__(self, _id, source, name, org_name, location, image_url, start_time, end_time, event_link, event_status,
                 theme, perks, food_related, popular, recurring, for_new_students, on_campus, religion):
        self._id = _id
        self.source = source
        self.name = name
        self.org_name = org_name
        self.location = location
        self.image_url = image_url
        self.start_time = start_time
        self.end_time = end_time
        self.event_link = event_link
        self.event_status = event_status  # 'in-person', 'online', 'hybrid'
        self.theme = theme  # academic, arts, athletics, career, community, cultural, fundraising, health, social, spirituality
        self.perks = perks  # free_food, free_stuff, credit, giveaway, prizes
        self.food_related = food_related
        self.popular = popular
        self.recurring = recurring
        self.for_new_students = for_new_students
        self.on_campus = on_campus
        self.religion = religion  # 'christian', 'jewish', 'muslim', 'hindu', None

    def get_end_timestamp(self):
        return round(self.end_time.timestamp()) if self.end_time else None

    def __eq__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        if self.source == other.source and self.source != "drexel_athletics":
            return self.org_name == other.org_name and (
                    self.start_time.timestamp() == other.start_time.timestamp() or self.get_end_timestamp() == other.get_end_timestamp())
        # only filter out events by the start time because duplicates can have different end times
        if self.start_time.timestamp() != other.start_time.timestamp() and self.get_end_timestamp() != other.get_end_timestamp():
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

    def to_sql(self):
        return (self._id, self.source, self.name, self.org_name, self.location, self.image_url,
                self.start_time.timestamp(), self.get_end_timestamp(), self.event_link, self.event_status, self.theme,
                "|".join(self.perks), self.food_related, self.popular, self.recurring, self.for_new_students,
                self.on_campus, self.religion)
