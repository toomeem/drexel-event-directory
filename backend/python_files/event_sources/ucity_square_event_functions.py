import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash

HTTP_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"}


class UCitySquareEventSource(EventSource):
    name = "ucity_square"
    priority = 3

    @staticmethod
    def _calendar_urls(months_out):
        base_calendar_url = "https://ucitysquare.com/events/month/"
        date_strings = []
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        for _ in range(months_out):
            date_strings.append(f"{current_year}-{current_month:02d}")
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        return [base_calendar_url + date_string for date_string in date_strings]

    @staticmethod
    def _is_past(tag):
        day_div = tag.parent.parent.parent
        tag_date = datetime.strptime(day_div.get("id"), "tribe-events-calendar-day-%Y-%m-%d")
        return tag_date < datetime.now()

    def _event_urls_from_calendar_page(self, url):
        response = requests.get(url, headers=HTTP_HEADER, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        events = soup.find_all("div", class_="tribe-events-calendar-month__calendar-event-details")
        return [event.contents[3].a["href"] for event in events if not self._is_past(event)]

    def _all_event_urls(self, months_out):
        event_urls = []
        for url in self._calendar_urls(months_out):
            event_urls.extend(self._event_urls_from_calendar_page(url))

        excluded_event_text = ["beer-garden", "cinespeak", "life-science-luncheon",
                               "fun-damentals-ucity-square-book-club/2026-09-16",
                               "summer-series"]
        return list({
            url for url in event_urls
            if not any(excluded_text in url for excluded_text in excluded_event_text)
        })

    @staticmethod
    def _match_default_image(name):
        lawn_image = "https://www.universitycity.org/wp-content/uploads/2026/03/original_images_106297125_3131683786946849_7604964815855804720_n_sjgx8c2w9.jpg"
        yoga_image = "https://www.eventbrite.com/e/_next/image?url=https%3A%2F%2Fimg.evbuc.com%2Fhttps%253A%252F%252Fcdn.evbuc.com%252Fimages%252F952808923%252F1814176558193%252F1%252Foriginal.20250204-222847%3Fcrop%3Dfocalpoint%26fit%3Dcrop%26w%3D1880%26auto%3Dformat%252Ccompress%26q%3D75%26sharp%3D10%26fp-x%3D0.5%26fp-y%3D0.5%26s%3De8039340c96baf2e46017e0bacae4c79&w=1880&q=75"
        food_truck_image = "https://ucitysquare.com/wp-content/uploads/2024/02/food-trucks.png"

        if "yoga" in name.lower():
            return yoga_image
        if "food truck" in name.lower():
            return food_truck_image
        return lawn_image

    @staticmethod
    def _get_event_data(url):
        time.sleep(1)
        response = requests.get(url, headers=HTTP_HEADER, timeout=30)
        if response.status_code == 429:
            time.sleep(30)
            response = requests.get(url, headers=HTTP_HEADER, timeout=30)
            if response.status_code == 429:
                print(f"Error: {response.status_code} - {url}")
                return None
            response = requests.get(url, headers=HTTP_HEADER, timeout=30)
        if response.status_code != 200:
            time.sleep(2)
            response = requests.get(url, headers=HTTP_HEADER, timeout=30)
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {url}")
                return None
        return response

    def collect(self):
        return [self._get_event_data(url) for url in self._all_event_urls(months_out=2)]

    def parse(self, response, event_fields):
        event_fields["_id"] = stable_hash(response.url)
        if event_fields["_id"] in self.existing_event_ids:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        now = datetime.now()

        time_str = soup.find("div", class_="tribe-events-schedule")
        time_str = time_str.text.strip().split("\n")[0].split(" ")
        month = time_str[0]
        day = time_str[1]
        start_time_str = time_str[3] + " " + time_str[4]
        end_time_str = time_str[6] + " " + time_str[7]
        year = now.year
        if datetime.strptime(month, "%B").month < now.month:
            year += 1
        format_str = "%Y %B %d %I:%M %p"
        event_fields["start_time"] = datetime.strptime(f"{year} {month} {day} {start_time_str}", format_str)
        event_fields["end_time"] = datetime.strptime(f"{year} {month} {day} {end_time_str}", format_str)

        event_fields["name"] = soup.find("h1").text
        description = soup.find("div", class_="tribe-events-single-event-description tribe-events-content")
        event_fields["description"] = description.text.strip().replace("\xa0", " ")
        event_fields["org_name"] = "uCity Square"
        if "The Lawn at uCity Square" in event_fields["description"]:
            event_fields["location"] = "The Lawn at uCity Square"
        else:
            event_fields["location"] = "3675 Market St"

        event_image = soup.find("div", class_="tribe-events-event-image")
        if event_image:
            event_fields["image_url"] = "https://ucitysquare.com" + event_image.find("img")["src"]
        else:
            event_fields["image_url"] = self._match_default_image(event_fields["name"])
        event_fields["event_link"] = response.url

        return event_fields
