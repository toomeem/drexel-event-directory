from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash


class BBJEventSource(EventSource):
    name = "bbj"
    priority = 0

    def collect(self):
        response = requests.get("https://blackbottomjazz.org/", timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.find_all("div", class_="event-card")

    def parse(self, event_data, event_fields):
        event_fields["_id"] = stable_hash(self.name + str(event_data.get("data-num")))
        if event_fields["_id"] in self.existing_event_ids:
            return None

        event_fields["name"] = event_data.find("h2").text
        event_fields["org_name"] = "The Black Bottom Lives On!"
        event_fields["location"] = event_data.find("p", class_="event-location").text.strip()
        event_fields[
            "image_url"] = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/images/default_images/bbj.jpeg"
        event_fields["event_link"] = "https://blackbottomjazz.org/"
        event_fields["event_status"] = "in-person"
        event_fields["theme"] = "cultural"
        event_fields["recurring"] = True

        date_str = event_data.find("p", class_="event-date-line").text.strip()
        date = datetime.strptime(date_str.split("•")[0].strip(), "%A, %B %d").replace(year=2026)
        time_range = date_str.split("•")[1].strip().split("–")
        try:
            start_time = datetime.strptime(time_range[0].strip(), "%I:%M %p")
            end_time = datetime.strptime(time_range[1].strip(), "%I:%M %p")
        except ValueError:
            start_time = datetime.strptime(time_range[0].strip(), "%I:%M") + timedelta(hours=12)
            end_time = datetime.strptime(time_range[1].strip(), "%I:%M %p")
        event_fields["start_time"] = datetime.combine(date.date(), start_time.time())
        event_fields["end_time"] = datetime.combine(date.date(), end_time.time())

        return event_fields
