class Event:
    def __init__(self, event_id, source, name, org_name, location, start_time, end_time, image_id):
        self.event_id = event_id
        self.source = source
        self.name = name
        self.org_name = org_name
        self.location = location
        self.start_time = start_time
        self.end_time = end_time
        self.image_id = image_id

    @classmethod
    def from_json(cls, event_json):
        if event_json["source"] == "dragonlink":
            return cls.from_dragonlink_json(event_json)

        if event_json["source"] == "drexel_events":
            return cls.from_drexel_events_json(event_json)

        raise ValueError("Unsupported event JSON format")

    @classmethod
    def from_dragonlink_json(cls, event_json):
        return cls(
            event_id=event_json["id"],
            source="dragonlink",
            name=event_json["name"],
            org_name=event_json["organizationName"],
            location=event_json["location"],
            start_time=event_json["startsOn"],
            end_time=event_json["endsOn"],
            image_id=event_json["imagePath"],
        )

    @classmethod
    def from_drexel_events_json(cls, event_json):
        if "deadline" in event_json["typeNames"].lower():
            return None
        department_names = event_json.get("departmentNames")

        return cls(
            event_id=event_json["id"],
            source="drexel_events",
            name=event_json["title"],
            org_name=department_names if department_names else "Drexel University",
            location=event_json["address"],
            start_time=event_json["startDate"],
            end_time=event_json["endDate"],
            image_id=event_json["image"],
        )

    @classmethod
    def from_drexel_athletics_json(cls, event_json):
        at_vs = event_json.get("atVs")
        opponent = event_json.get("opponent").get("title")
        default_image = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/drexeldragons.com/images/sng_2023/footer_reccenter.png"
        return cls(
            event_id=event_json["id"],
            source="drexel_athletics",
            name=" ".join(["DREX", at_vs, opponent]),
            org_name=event_json["sport"]["title"],
            location=event_json["location"],
            start_time=event_json["dateUtc"],
            end_time=event_json["endDateUtc"],
            image_id=default_image,  # TODO: get images for each sport
        )