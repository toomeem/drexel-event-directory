import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

import requests
from backend.python_files.event_class import Event
from backend.python_files.helper_functions import stable_hash, is_food_related, is_recurring
from backend.python_files.image_parsing_functions import get_image_s3_url


def get_ucity_square_calendar_urls(months_out):
    base_calendar_url = "https://ucitysquare.com/events/month/"
    date_strings = []
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    i = 0
    while i < months_out:
        date_strings.append(f"{current_year}-{current_month:02d}")
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
        i += 1

    return [base_calendar_url + date_string for date_string in date_strings]


def get_all_ucity_square_urls(months_out):
    calendar_urls = get_ucity_square_calendar_urls(months_out)
    event_urls = []
    for url in calendar_urls:
        event_urls.extend(get_event_urls_from_calendar_page(url))
    event_urls = list(set(event_urls))
    return event_urls


def get_event_urls_from_calendar_page(url):
    def is_past(tag):
        day_div = tag.parent.parent.parent
        tag_date = datetime.strptime(day_div.get("id"), "tribe-events-calendar-day-%Y-%m-%d")
        return tag_date < datetime.now()

    event_links = []
    response = requests.get(url, headers=http_header)
    soup = BeautifulSoup(response.text, "html.parser")
    events = soup.find_all("div", class_="tribe-events-calendar-month__calendar-event-details")

    for event in events:
        if is_past(event):
            continue
        event_links.append(event.contents[3].a["href"])
    return event_links


def match_ucity_square_default_image(name, location):
    ucity_square_lawn_default_image = "https://www.universitycity.org/wp-content/uploads/2026/03/original_images_106297125_3131683786946849_7604964815855804720_n_sjgx8c2w9.jpg"
    yoga_image = "https://www.eventbrite.com/e/_next/image?url=https%3A%2F%2Fimg.evbuc.com%2Fhttps%253A%252F%252Fcdn.evbuc.com%252Fimages%252F952808923%252F1814176558193%252F1%252Foriginal.20250204-222847%3Fcrop%3Dfocalpoint%26fit%3Dcrop%26w%3D1880%26auto%3Dformat%252Ccompress%26q%3D75%26sharp%3D10%26fp-x%3D0.5%26fp-y%3D0.5%26s%3De8039340c96baf2e46017e0bacae4c79&w=1880&q=75"
    beer_garden_image = "https://www.universitycity.org/wp-content/uploads/2026/03/UCDSummerSeries2025_Final_181.jpg"
    food_truck_image = "https://ucitysquare.com/wp-content/uploads/2024/02/food-trucks.png"
    the_3675_market_st_image = "https://ucitysquare.com/wp-content/uploads/2023/09/S-3675-Market-3-1600x1600.webp"
    if "yoga" in name.lower():
        return yoga_image
    if "beer garden" in name.lower():
        return beer_garden_image
    if "food truck" in name.lower():
        return food_truck_image
    if location == "3675 Market St":
        return the_3675_market_st_image
    return ucity_square_lawn_default_image


def match_ucity_square_event_theme(name, description):
    # academic, arts, athletics, career, community, cultural, fundraising, health, social, spirituality
    theme_keyword_match = {"yoga": "athletics", "beer garden": "social", "food truck": "social",
                           "innovation exchange": "career", "life sciences": "academic",
                           "embroidery workshop": "arts", "reset lab": "health", "asl": "arts",
                           "retention by design": "career",
                           "university city summer series concert": "arts", "creativemornings": "community",
                           "monthly innovation exchange": "career"}
    for keyword, theme in theme_keyword_match.items():
        if keyword in name.lower() or keyword in description.lower():
            return theme
    return "social"


def simplify_ucity_square_event_name(name):
    remove_list = ["– Spring", "– Summer", "– Fall", "– Winter", "at The Lawn", "()", "  "]
    for remove_str in remove_list:
        name = name.replace(remove_str, "")
    return name.strip()


def get_ucity_square_event_perks(name):
    free_food_events = ["life sciences luncheon"]
    free_stuff_events = ["stay flossy: embroidery workshop"]
    perks = []

    if name.lower() in free_food_events:
        perks.append("free_food")
    if name.lower() in free_stuff_events:
        perks.append("free_stuff")
    return perks


def create_ucity_square_event_from_url(url, bucket_name):
    kwargs = {"_id": stable_hash(url), "source": "ucity_square", "name": None, "org_name": "uCity Square",
              "location": None, "image_url": None, "start_time": None, "end_time": None,
              "event_link": url, "event_status": "in-person", "theme": None, "perks": [], "food_related": False,
              "popular": False, "recurring": False, "for_new_students": False, "on_campus": True, "religion": None,
              "description": ""}

    request_wait_time = 0.3
    time.sleep(request_wait_time)

    response = requests.get(url, headers=http_header)
    if response.status_code == 429:
        print("Got rate limited, sleeping for 5 seconds")
        time.sleep(5)
        response = requests.get(url, headers=http_header)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {url}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    now = datetime.now()
    time_str = soup.find("div", class_="tribe-events-schedule")
    if time_str is None:
        print(f"Error: {url}")
        return None
    time_str = time_str.text.strip().split("\n")[0].split(" ")
    month = time_str[0]
    day = time_str[1]
    start_time_str = time_str[3] + " " + time_str[4]
    end_time_str = time_str[6] + " " + time_str[7]
    year = now.year
    if datetime.strptime(month, "%B").month < now.month:
        year += 1
    format_str = "%Y %B %d %I:%M %p"
    kwargs["start_time"] = datetime.strptime(f"{year} {month} {day} {start_time_str}", format_str)
    kwargs["end_time"] = datetime.strptime(f"{year} {month} {day} {end_time_str}", format_str)

    if kwargs["end_time"] < (now + timedelta(hours=1)):
        return None

    kwargs["name"] = simplify_ucity_square_event_name(soup.find("h1").text)
    description = soup.find("div", class_="tribe-events-single-event-description tribe-events-content")
    if description is None:
        print(url)
        exit(1)
    description = description.text.strip().replace("\xa0", " ")
    kwargs["description"] = description
    if "The Lawn at uCity Square" in description or "Beer Garden" in kwargs["name"]:
        kwargs["location"] = "The Lawn at uCity Square"
    else:
        kwargs["location"] = "3675 Market St"

    event_image_url = soup.find("div", class_="tribe-events-event-image")
    if event_image_url:
        image_base_url = "https://ucitysquare.com"
        original_image_url = image_base_url + event_image_url.find("img")["src"]
    else:
        original_image_url = match_ucity_square_default_image(kwargs["name"], kwargs["location"])
    kwargs["image_url"] = get_image_s3_url(original_image_url, bucket_name)

    kwargs["theme"] = match_ucity_square_event_theme(kwargs["name"], kwargs["description"])
    kwargs["perks"] = get_ucity_square_event_perks(kwargs["name"])
    kwargs["recurring"] = is_recurring(kwargs["name"], kwargs["description"])
    kwargs["food_related"] = is_food_related(kwargs["name"], kwargs["perks"], kwargs["location"], kwargs["description"])

    del kwargs["description"]
    return Event(**kwargs)


http_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"}
