import json
import os
import time
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from openai import OpenAI
from pydantic import BaseModel

import boto3
import psycopg2
import requests
from dotenv import load_dotenv
from event_class import Event

PHILLY_TZ = ZoneInfo("America/New_York")
HTTP_TIMEOUT = (5, 30)


class OnlineStatus(BaseModel):
    event_status: str  # in-person, virtual, hybrid
    physical_location: str


def _fmt_hm(dt, with_ampm=False):
    h = dt.strftime("%I").lstrip("0") or "12"
    return f"{h}:{dt.strftime('%M %p')}" if with_ampm else f"{h}:{dt.strftime('%M')}"


def make_time_str(start_time, end_time):
    start_time = start_time.replace(tzinfo=PHILLY_TZ)
    end_time = end_time.replace(tzinfo=PHILLY_TZ)
    now = datetime.now(PHILLY_TZ)
    if end_time - start_time > timedelta(hours=24):
        if (start_time - now) > timedelta(days=7):
            return datetime.strftime(start_time, "%a - ") + datetime.strftime(end_time, "%a")
        return f"{start_time.strftime('%b')} {start_time.day} - {end_time.day}"

    if now.strftime("%m/%d") == start_time.strftime("%m/%d"):
        time_str_prefix = "Today"
    elif (now + timedelta(days=1)).strftime("%m/%d") == start_time.strftime("%m/%d"):
        time_str_prefix = "Tmrw"
    elif (start_time - now) > timedelta(days=7):
        time_str_prefix = f"{start_time.strftime('%b')} {start_time.day}"
    else:
        time_str_prefix = datetime.strftime(start_time, "%a")
    return f"{time_str_prefix} - {_fmt_hm(start_time)}-{_fmt_hm(end_time, with_ampm=True)}"


def normalize_time(source, time_str):
    if not time_str:
        return None
    if source == "drexel_athletics":
        time_str = time_str.replace("Z", "")
    dt = datetime.fromisoformat(time_str)
    return dt


def simplify_location(location):
    if not location:
        return None
    if "cancelled" in location.lower():
        return None

    online_placeholders = ["online", "remote", "virtual", "virtual event", "zoom"]
    if location.lower() in online_placeholders:
        return "Online"

    strip_chars = " ,.-*"
    total_replace_list = {"Nesbitt 140": "Nesbitt Collaboratory", "Nesbitt Collaboratory": "Nesbitt Collaboratory",
                          "Nesbitt Hall, Collaboratory": "Nesbitt Collaboratory",
                          "Rincliffe Gallery": "Rincliffe Gallery", "Pearlstein Gallery": "Pearlstein Gallery",
                          "Peck Alumni Center Gallery": "Peck Alumni Center Gallery", "Lanc Walk": "Lancaster Walk",
                          "Lancaster Walk": "Lancaster Walk", "Hagerty Library": "Hagerty Library",
                          "Hagerty": "Hagerty Library", "A. J. Drexel Picture Gallery": "A. J. Drexel Picture Gallery",
                          "A.J. Drexel Picture Gallery": "A. J. Drexel Picture Gallery",
                          "Anthony J. Drexel Picture Gallery": "A. J. Drexel Picture Gallery",
                          "AJ Drexel Picture Gallery": "A. J. Drexel Picture Gallery",
                          "Lockheed Martin Launchpad": "Lockheed Martin Launchpad", "Online Event": "Online",
                          "Zoom": "Online", "Geary Auditorium": "Geary Auditorium",
                          "Mandell Theater": "Mandell Theater", "Drexel Park": "Drexel Park",
                          "Education Abroad Office": "Education Abroad Office",
                          "Academic Building Suite 201": "Education Abroad Office",
                          "Hill Seminar Room": "Hill Seminar Room", "LeBow Eng. 240": "Hill Seminar Room",
                          "Lindy Center for Civic Engagement": "Lindy Center", "The Lindy Center": "Lindy Center",
                          "NSBITT 111": "NSBITT Stein Auditorium", "Stein Auditorium": "NSBITT Stein Auditorium",
                          "NSBITT 125 - Ruth Auditorium": "NSBITT Ruth Auditorium", "Korman Quad": "Korman Quad",
                          "Humpty Dumplings Glenside": "Humpty Dumplings", "Register on Handshake": "Online",
                          "zoom:": "Online", "The Kimmel Center": "The Kimmel Center", "Penny Park": "Penny Park",
                          "Mitchell Auditorium": "BSONE Mitchell Auditorium",
                          "Penn's Landing 401 S Christopher Columbus Blvd": "Penn's Landing",

                          "Cancer Center at the Thomas Jefferson University": "Cancer Center at the Thomas Jefferson University",
                          "URBN Annex Screening Room": "URBN Screening Room",
                          "MAIN - Auditorium": "Main Building Auditorium",
                          "Main Auditorium": "Main Building Auditorium",
                          "Main Auditorium in Main Building": "Main Building Auditorium",
                          "Main Auditorium\r\nMain Building": "Main Building Auditorium",
                          "The Academy of Natural Sciences": "The Academy of Natural Sciences",
                          "The Curtis Atrium": "The Curtis Atrium", "Black Box Theater": "URBN Black Box Theater",
                          "Dornsife Center for Neighborhood Partnership": "Dornsife Center",
                          "Highmark Mann Center": "Highmark Mann Center",
                          "Mack Miles Playground": "Mack Miles Playground",
                          "Office of Graduate Studies": "Office of Graduate Studies",
                          "Office of Graduate Students": "Office of Graduate Studies",
                          "Elkin's Park Parking Lot": "Elkin's Park Parking Lot", "Dragon Statue": "Dragon Statue"}
    suffixes = [" - Classroom w/ 14 PCs", " - Classroom w/ 6 PCs", " - Classroom w/ 8 PCs", " - COM Classroom",
                " - Classroom", " - Roberta Rosen Sheller Chapel", " - Auditorium", " - Conference",
                "- 1st Floor Exclusive", "(Section 1)", "(2nd Floor)", "(4th Floor)", "(6th Floor)", "(Exclusive)",
                "- All Sections", "- Danzinger Conference Room", "(212 - Chapel, 211 - Office)"]
    remove_list = ["\r", "\r", "\r", "\r", "\n", "\n", "\n", "\n", "Pa 19104", "Pa 19103", "Pa 19106", "19103", "19104",
                   "19106", "Philadelphia", ", PA", "located at the northeast corner of 33rd and Chestnut Streets",
                   "located at 32nd and Market Streets", "101 N 33rd St", "(Main 010 A)", "located at",
                   "3230 Market Street", "- Group Exercise Studio -", "RSVP Required to Attend", "60 N. 36th Street",
                   "33rd and Market Street", ", USA", "(if rain-W106)", "3501 Market Street", "3401 Filbert Street",
                   "3200 Chestnut Street", "3200 Chestnut St", "3141 Chestnut Street", "3141 Chestnut St",
                   "Table Space 1 -", "Table Space 1", "Table Space 2 -", "Table Space 2",
                   "one block north of Market Street", "located at 60 N. 36th Street", " - Class Lab",
                   "3509 Spring Garden St", "60 N 36th St.", "3675 Market Street", "(15 Wellness Points)"]
    replace_list = [(" Streets", " St"), (" Street", " St"), ("\n", " "),
                    ("Papadakis Integrated Sciences Building", "PISB"), ("College of Computing & Informatics", "CCI"),
                    ("Creese Student Center", "CREESE"), ("Drexel University Campus", "Drexel Campus"),
                    ("Bossone Research and Enterprise Center", "BSONE"), ("Bossone Research Center", "BSONE"),
                    ("Rush building", "RUSH"), ("Rush Building", "RUSH"), (" - Alumni Garden", " Garden"),
                    ("Pearlstein Business Learning Center", "PEARL"), ("Nesbitt Hall", "NSBITT"),
                    ("Great Court (Exclusive)", "Great Court"), ("Academic Building", "ACADMC"),
                    ("Gerri C. LeBow Hall", "LEBOW"), ("Drexel Health Sciences Building", "HSB"),
                    ("Health Sciences Building", "HSB"), ("Daskalakis Athletic Center", "DAC"), ("(,", "("),
                    (",)", ")"), (" )", ")"), (" )", ")"), ("()", ""), (" , ", " "), ("  ", " "), ("  ", " "),
                    ("  ", " "), ]
    building_shortnames = ["PISB", "CREESE", "BSONE", "RUSH", "ACADMC", "RANDEL", "RANDELL", "GHALL", "MAIN", "URBN",
                           "URBN", "PEARL", "CAT", "NSBITT", "Korman", "HSB", "ROSS", "LEBOW", "LeBow", "JEMIC", "CCI",
                           "DAC"]

    for k, v in total_replace_list.items():
        if k in location:
            return v
    location = location.strip(strip_chars)
    for suffix in suffixes:
        location = location.removesuffix(suffix)
    for i in remove_list:
        location = location.replace(i, "", 1)
    for old, new in replace_list:
        location = location.replace(old, new)
    location = location.strip(strip_chars)
    for i in building_shortnames:
        if i in location:
            location = location.replace(f"({i})", "", 1).replace(f"{i} Center", i, 1).replace(f"{i} center", i, 1)
            location = (
                location.replace(f"{i}, Room", i, 1).replace(f"{i}, room", i, 1).replace(f"{i} - Room", i, 1).replace(
                    f"{i} - room", i, 1).replace(f"{i} Room", i, 1).replace(f"{i} room", i, 1).replace(f"{i}Room", i,
                                                                                                       1).replace(
                    f"{i}room", i, 1).replace(f"{i} Suite", i, 1).replace(f"{i} Meeting room", i, 1).replace(
                    f"{i} Meeting Room", i).replace(f"{i} meeting room", i, 1).replace(f"{i},", i, 1))

            break
    return location.strip()


def match_default_image(name, org_name, location):
    name = name.lower() if name else ""
    org_name = org_name.lower() if org_name else ""
    location = location.lower() if location else ""
    drexel_default_image = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/home/where-dragons-soar/lancasterwalk-area-lawn-3200x1600_16x9/lancasterwalk-area-lawn-3200x1600_16x9_16x9.jpg"
    pearlstein_image = "https://drexel.edu/news/~/media/Drexel/Core-Site-Group/News/Images/v2/story-images/2022/March/Pearlstein_gallery96-copy/pearlstein_gallery96-copy_16x9.jpg?w=3200&hash=E14D6C3BEF38BF17CAAD5EABC5C9162F"
    westphal_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQejsADyZdJy0QWh6odgCt42Bw9A5fsAPtXMg&s"
    dac_image = "https://www.sasaki.com/wp-content/uploads/2019/10/TurDRC09_website-1800x1350.jpg"
    main_building_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Main_Building_-_Drexel_University_%2853590618820%29.jpg/250px-Main_Building_-_Drexel_University_%2853590618820%29.jpg"
    hagerty_library_image = "https://pbs.twimg.com/media/G8D-sieWQAMOGeO.jpg"
    korman_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3qHPfEMM3sZWBAwamvamv8lvT4LzQmfcwQw&s"
    pisb_image = "https://www.architectmagazine.com/wp-content/uploads/sites/5/2013/616a38fa-c2f8-4e1f-85e3-e23d8bcb9126.jpg"
    rush_building = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/admissions/virtual-tour/rush-building.jpg"
    med_building = "https://www.salus.edu/news-stories/_files/images/drexel-nursing-building-pic1.jpg"
    image_aliases = {"pearlstein gallery": pearlstein_image, "westphal": westphal_image, "dac": dac_image,
                     "rec center": dac_image, "main building": main_building_image, "hagerty": hagerty_library_image,
                     "korman": korman_image, "pisb": pisb_image, "papadakis": pisb_image, "science": pisb_image,
                     "rush": rush_building, "lancaster": drexel_default_image, "nursing": med_building,
                     "medicine": med_building, }
    for key, image in image_aliases.items():
        if key in name or key in org_name or key in location:
            return image
    return drexel_default_image


_online_status_cache = {}


def get_online_status(client, location):
    if location in _online_status_cache:
        return _online_status_cache[location]
    response = client.chat.completions.parse(model="gpt-5-nano-2025-08-07", messages=[{"role": "system", "content": '''
                        You are an expert at structured data extraction.
                        You will be given information about the location of an event on Drexel University's campus and your task is to determine whether the event is hybrid, virtual or in-person.
                        If an event is virtual, it will explicitly state that is is event_status/virtual and will likely say 'zoom' or 'meet'. If it doesn't clearly state that it is virtual, you will assume it is in-person.
                        You will first select the 'event_status' field. Here are the only allowed responses for the event_status field: ['in-person', 'virtual', 'hybrid'].
                        If the event is hybrid, It will explicitly state a physical location and that it is virtual/event_status. I will most likely signal this using 'and'/'&' or 'or' to show that there are multiple options. Example 'PISB 108 & Online'
                        For hybrid events, for the 'physical_location' parameter just return the physical location and ignore any information about the virtual aspect of the event. For in-person events, just return the location as the 'physical_location' and for virtual events, return 'N/A' for the physical location.
                 ''', }, {"role": "user", "content": location}, ], response_format=OnlineStatus, )
    response_object = response.choices[0].message.parsed
    result = {"event_status": response_object.event_status, "physical_location": response_object.physical_location}
    _online_status_cache[location] = result
    return result


def dragonlink_event_parsing(event_json, kwargs):
    source = "dragonlink"
    dragonlink_base_url = "https://drexel.campuslabs.com/engage/"
    dragonlink_image_url = dragonlink_base_url + "image/"
    dragonlink_event_url = dragonlink_base_url + "event/"
    specific_events_to_exclude = ["12449523", "12449521"]

    if str(event_json["id"]) in specific_events_to_exclude:
        return None
    kwargs["name"] = event_json["name"]
    kwargs["org_name"] = event_json["organizationName"]
    kwargs["location"] = event_json["location"]
    kwargs["start_time"] = normalize_time(source, event_json["startsOn"])
    kwargs["end_time"] = normalize_time(source, event_json["endsOn"])

    if event_json["imagePath"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["imagePath"]
    elif event_json["organizationProfilePicture"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["organizationProfilePicture"]
    kwargs["event_link"] = dragonlink_event_url + event_json["id"]

    religious_orgs = ["Jewish Student Association", "Drexel Muslim Students Association", "Every Nation Campus",
                      "Drexel Asian Baptist Student Koinonia", "Story Fellowship", "Cru",
                      "Drexel Newman Catholic Community", "Crosswalk Christian Fellowship", "Drexel WEH",
                      "Hindu YUVA @ Drexel", "Open Door Christian Community ", "Drexel Students for Christ"]
    athletics_keywords = ["pilates", "bhangra", "yoga", "zumba", "salsa", "spikeball", "spike ball",
                          "drexel dragon jedi meeting", "kayaking", "paintball", "hike", "hiking", "skiing",
                          "snowboarding", "rafting", "horseback riding", "paddleboarding", "canoeing", "canoe",
                          "surfing", "scuba", "biking", "dance workshop", "dance class", "sumo night"]

    if kwargs["org_name"] in religious_orgs:
        kwargs["theme"] = "spirituality"
    elif kwargs["org_name"] == "Weekend Warriors":
        kwargs["theme"] = "athletics"
    elif any([keyword in kwargs["name"].lower() for keyword in athletics_keywords]):
        kwargs["theme"] = "athletics"
    elif event_json["theme"] in ["Arts", "Athletics", "Cultural", "Fundraising", "Social", "Spirituality"]:
        kwargs["theme"] = event_json["theme"].lower()
    elif "Credit" in event_json["categoryNames"] or event_json["theme"] == "CommunityService":
        kwargs["theme"] = "community"
    elif "Philanthropy" in event_json["categoryNames"] or "Fundraising" in event_json["categoryNames"]:
        kwargs["theme"] = "fundraising"
    elif "Social" in event_json["categoryNames"] or "Fraternity and Sorority Life" in event_json["categoryNames"]:
        kwargs["theme"] = "social"
    elif "Professional Development/Leadership" in event_json["categoryNames"] or "Leadership Development" in event_json[
        "categoryNames"] or "Networking" in event_json["categoryNames"]:
        kwargs["theme"] = "career"
    elif "Academic" in event_json["categoryNames"] or "Educational" in event_json["categoryNames"]:
        kwargs["theme"] = "academic"
    elif "Residence Life - Community and Civic Engagement" in event_json["categoryNames"]:
        kwargs["theme"] = "community"
    else:
        kwargs["theme"] = "social"

    kwargs["perks"] = [i.lower().replace(" ", "_") for i in event_json["benefitNames"]]
    kwargs["theme"] = kwargs["theme"].lower()
    return kwargs


def drexel_event_parsing(event_json, kwargs):
    source = "drexel_events"
    if "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
        return None
    authors = event_json.get("authors")
    department_names = event_json.get("departmentNames")
    if authors:
        kwargs["org_name"] = authors[0]
    elif department_names:
        kwargs["org_name"] = department_names[0]
    else:
        kwargs["org_name"] = "Drexel University"

    kwargs["name"] = event_json["title"]
    kwargs["location"] = event_json["address"]
    if "<a" in kwargs["location"]:
        kwargs["location"] = kwargs["location"].split("<a")[0].strip()
    kwargs["start_time"] = normalize_time(source, event_json["startDate"])
    kwargs["end_time"] = normalize_time(source, event_json["endDate"])
    kwargs["event_link"] = event_json["contentUrl"]
    if event_json["image"]:
        kwargs["image_url"] = event_json["image"]

    type_names = event_json.get("typeNames") or []
    department_names = event_json.get("departmentNames") or []
    if "Exhibit" in type_names or "Performing Arts" in department_names:
        kwargs["theme"] = "arts"
    elif "Academic Events" in type_names or "Academic Support" in type_names:
        kwargs["theme"] = "academic"
    elif "SCDC: Information Sessions" in type_names or "SCDC: Workshops" in type_names:
        kwargs["theme"] = "academic"
    elif "Co-op & Career Development" in type_names or "Lectures" in type_names:
        kwargs["theme"] = "academic"
    elif "Diversity & Inclusion" in type_names:
        kwargs["theme"] = "cultural"
    elif "Community Service" in type_names or "Civic Engagement" in type_names:
        kwargs["theme"] = "community"
    elif "ANS: Museum Activities" in type_names:
        kwargs["theme"] = "social"
    elif "Student Life & Organizations" in type_names:
        kwargs["theme"] = "social"
    elif "Seminars" in type_names:
        kwargs["theme"] = "academic"
    else:
        kwargs["theme"] = "social"

    features = event_json.get("features") or []
    for feature in features:
        if feature == "Giveaways":
            kwargs["perks"].append("free_stuff")
        elif "credit" in feature.lower() or feature == "CEU Available":
            kwargs["perks"].append("credit")
        elif feature == "Free Food":
            kwargs["perks"].append("free_food")

    unknown_perks = [f for f in features if
                     f and f not in ("Free Food", "Free Stuff", "Credit", "Online Access", "Giveaways",
                                     "CEU Available")]
    if unknown_perks:
        print(f"Unknown perk: {unknown_perks}")

    return kwargs


def drexel_athletics_event_parsing(event_json, kwargs):
    source = "drexel_athletics"
    drexel_athletics_image = "https://drexel.edu/identity/~/media/Drexel/UMaC-Site-Group/Identity/Images/athletics/resized_logos/Athletics-Wordmark-DU-Blue-yellow-3200x1800-Identity-Images.jpg"
    drexel_athletics_schedule_url = "https://drexeldragons.com/sports/"
    drexel_athletics_aliases = {"mbball": "mens-basketball", "wbball": "womens-basketball", "mgolf": "mens-golf",
                                "mlax": "mens-lacrosse", "wlax": "womens-lacrosse", "mcrew": "mens-crew",
                                "wcrew": "womens-crew", "msoc": "mens-soccer", "wsoc": "womens-soccer",
                                "msquash": "mens-squash", "wsquash": "womens-squash",
                                "mswim": "mens-swimming-and-diving", "wswim": "womens-swimming-and-diving",
                                "mten": "mens-tennis", "wten": "womens-tennis", "wrestling": "wrestling",
                                "fhockey": "field-hockey", "softball": "softball", }

    at_vs = event_json["atVs"]
    opponent = event_json["opponent"]["title"]
    sport_short_raw = event_json["sport"]["globalSportShortname"]
    sport_shorthand = drexel_athletics_aliases.get(sport_short_raw)
    if sport_shorthand is None:
        print(f"Unknown athletics sport shortname: {sport_short_raw}")
        sport_shorthand = sport_short_raw

    kwargs["name"] = " ".join(["DREX", at_vs, opponent])
    kwargs["org_name"] = f"Drexel {event_json['sport']['title']}"
    kwargs["location"] = event_json["location"]
    kwargs["start_time"] = normalize_time(source, event_json["dateUtc"])
    kwargs["end_time"] = normalize_time(source, event_json["endDateUtc"])
    kwargs["image_url"] = drexel_athletics_image
    kwargs["event_link"] = drexel_athletics_schedule_url + sport_shorthand + "/schedule"
    kwargs["theme"] = "athletics"
    kwargs["perks"] = []
    return kwargs


def create_event_object(source, event_json, client):
    online_keywords = ["zoom", "virtual", "hybrid", "handshake", "online", "remote"]
    online_location_default_text = "Online"
    exclude_events = ["Drexel FSAE Sping GBM 2025", "Study Hours", "Drexel University Circle K General Body Meeting",
                      "Ukranian Non-Profit Physical Goods Drive", "Dorm Objects 101",
                      "Visualizing Health: A Photography Exhibit", "Graduate Student Writing Group",
                      "Dorm Objects 101 Guided Tours", "GBM #5",
                      "Exploring National Anniversaries Through the Atwater Kent Collection at Drexel",
                      "Recognition Office Hours", "Chapter", "UREP Drop-In Hours", "SASE Spring Term E-board Meetings",
                      "SWE Spring 2026 Officer Meetings"]
    kwargs = {"_id": None, "source": source, "name": None, "org_name": None, "location": None, "image_url": None,
              "start_time": None, "end_time": None, "event_link": None, "event_status": None, "theme": None,
              "perks": [], }

    match source:
        case "dragonlink":
            kwargs = dragonlink_event_parsing(event_json, kwargs)
        case "drexel_events":
            kwargs = drexel_event_parsing(event_json, kwargs)
        case "drexel_athletics":
            kwargs = drexel_athletics_event_parsing(event_json, kwargs)
        case _:
            return None
    if kwargs is None:
        return None

    if not all([kwargs["start_time"], kwargs["end_time"], kwargs["name"], kwargs["org_name"], kwargs["location"]]):
        return None
    if kwargs["name"] in exclude_events:
        return None
    if "general body meeting" in kwargs["name"].lower() or "gbm" in kwargs["name"].lower() or "chapter meeting" in \
            kwargs["name"].lower():
        return None
    if kwargs["name"].startswith("CANCELLED"):
        return None

    kwargs["_id"] = str(uuid.uuid7().hex)
    if kwargs["image_url"] is None:
        kwargs["image_url"] = match_default_image(kwargs["name"], kwargs["org_name"], kwargs["location"])

    if source == "drexel_athletics":
        kwargs["event_status"] = "in-person"
    elif kwargs["location"] == online_location_default_text:
        kwargs["event_status"] = "virtual"
    elif "and virtual" in kwargs["location"]:
        kwargs["event_status"] = "hybrid"
    elif any(keyword in str(kwargs["location"]).lower() for keyword in online_keywords):
        online_status_response = get_online_status(client, kwargs["location"])
        kwargs["event_status"] = online_status_response["event_status"]
        if kwargs["event_status"] == "hybrid":
            kwargs["location"] = online_status_response["physical_location"]
        elif kwargs["event_status"] == "virtual":
            kwargs["location"] = online_location_default_text
    else:
        kwargs["event_status"] = "in-person"

    kwargs["location"] = simplify_location(kwargs["location"])
    if kwargs["location"] is None:
        return None
    if kwargs["location"] == "Online":
        kwargs["event_status"] = "virtual"

    org_name_remove = ["Drexel Chapter", "Drexel University Chapter", "Drexel Student Chapter",
                       "Drexel University Student Chapter", "Gamma Chapter", "Drexel Section", "at Drexel University",
                       "(CCMADS)", "Shake Team", "&amp", "Philadelphia City Chapter", "at Drexel", "(USGO)",
                       "Incorporated", "Inc.", "Student Group", ", ,"]
    if kwargs["org_name"].startswith("Drexel University"):
        kwargs["org_name"] = kwargs["org_name"].replace("Drexel University", "", 1)
    for i in org_name_remove:
        kwargs["org_name"] = kwargs["org_name"].replace(i, "", 1)
    kwargs["org_name"] = kwargs["org_name"].strip(";-,. ")

    return Event(**kwargs)


def create_dragonlink_api_url(count):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
    base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
    return base_url + "?endsAfter=" + timestamp + base_filters + str(count)


def collect_dragonlink_events(count=300):
    response = requests.get(create_dragonlink_api_url(count), timeout=HTTP_TIMEOUT).json()

    os.makedirs("json_examples", exist_ok=True)
    with open("json_examples/dragonlink_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4)

    return response["value"]


def create_drexel_events_api_url(page=1):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def collect_drexel_events(count=200):
    results = []
    for i in range(count // 10):
        response = requests.get(create_drexel_events_api_url(i + 1), timeout=HTTP_TIMEOUT)
        results.extend(dict(response.json())["results"])
        time.sleep(.1)

    os.makedirs("json_examples", exist_ok=True)
    with open("json_examples/drexel_events_response.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    return results


def create_drexel_athletics_api_url(days_out=90):
    now = datetime.now()
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def create_drexel_athletics_events():
    url = create_drexel_athletics_api_url()
    response = requests.get(url, timeout=HTTP_TIMEOUT)

    response_json = list(response.json())
    events_json = []

    for day in response_json:
        if day["events"] is None:
            continue
        for event in day["events"]:
            events_json.append(event)

    os.makedirs("json_examples", exist_ok=True)
    with open("json_examples/drexel_athletics_response.json", "w", encoding="utf-8") as f:
        json.dump(events_json, f, indent=4)

    return events_json


def create_event_chunk_file(event):
    path = "chunking_tmp_dir/" + event._id + ".json"
    event_json = event.to_json()
    event_json["formatted_time_str"] = make_time_str(event.start_time, event.end_time)
    del event_json["event_link"]
    del event_json["image_url"]
    del event_json["id"]
    del event_json["start_time"]
    del event_json["end_time"]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(event_json, f)


def clear_tmp_dir():
    path = "chunking_tmp_dir/"
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


def clear_s3_folder(bucket):
    folder_path = "chunked/"
    bucket.objects.filter(Prefix=folder_path).delete()


def upload_file_to_s3(bucket, file_name):
    local_file_path = "chunking_tmp_dir/" + file_name + ".json"
    s3_file_path = "chunked/" + file_name + ".json"
    bucket.upload_file(local_file_path, s3_file_path)


def sync_s3_knowledge_base():
    client = boto3.client("bedrock-agent", aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")
    client.start_ingestion_job(knowledgeBaseId=os.getenv("AWS_BEDROCK_KNOWLEDGE_BASE_ID"),
                               dataSourceId=os.getenv("AWS_BEDROCK_DATA_SOURCE_ID"))


def collect_all_events(client):
    events = []
    events.extend([create_event_object("dragonlink", event_json, client) for event_json in collect_dragonlink_events()])
    events.extend([create_event_object("drexel_events", event_json, client) for event_json in collect_drexel_events()])
    events.extend([create_event_object("drexel_athletics", event_json, client) for event_json in
                   create_drexel_athletics_events()])

    events = [e for e in events if e is not None and e.start_time is not None]

    source_priority = {"drexel_events": 0, "drexel_athletics": 1, "dragonlink": 2}

    # group possible duplicates by start time first
    by_start = {}
    for e in events:
        by_start.setdefault(e.get_start_timestamp(), []).append(e)

    result = []
    for candidates in by_start.values():
        clusters = []
        for event in candidates:
            for cluster in clusters:
                if any(event == existing for existing in cluster):
                    cluster.append(event)
                    break
            else:
                clusters.append([event])

        for cluster in clusters:
            result.append(max(cluster, key=lambda e: source_priority.get(e.source, -1)))

    result.sort(key=lambda e: e.get_start_timestamp())
    return result


def load_events_from_file(path="events.json"):
    with open(path, encoding="utf-8") as f:
        events_json = json.load(f)
    events = []
    for e in events_json:
        events.append(
            Event(_id=e["id"], source=e["source"], name=e["name"], org_name=e["org_name"], location=e["location"],
                  image_url=e["image_url"],
                  start_time=datetime.fromtimestamp(e["start_time"]) if e["start_time"] else None,
                  end_time=datetime.fromtimestamp(e["end_time"]) if e["end_time"] else None, event_link=e["event_link"],
                  event_status=e["event_status"], theme=e["theme"], perks=e["perks"], ))
    return events


def save_events_to_file(events):
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump([event.to_json() for event in events], f, indent=4)


def save_events_to_db(events):
    with psycopg2.connect(host=os.getenv("RDS_ENDPOINT"), database="postgres", user=os.getenv("RDS_USERNAME"),
                          password=os.getenv("RDS_PASSWORD"), port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE main.events")
            cursor.executemany('''
                               INSERT INTO main.events(id, source, name, org_name, location, image_url, start_time,
                                                       end_time,
                                                       event_link, event_status, theme, perks)
                               VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), to_timestamp(%s), %s, %s, %s, %s)
                               ''', [(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11]) for e in
                                     [event.to_sql() for event in events]])


def fill_db():
    events = load_events_from_file()
    print(f"\nUploading {len(events)} events to database...")
    save_events_to_db(events)


def update_events_file(client):
    print("\nCollecting events...")
    events = collect_all_events(client)
    save_events_to_file(events)
    print(f"\nSaved {len(events)} events to file.")


def upload_all_events_to_s3():
    print("\nUploading events to S3...")

    s3 = boto3.resource(service_name='s3', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
    bucket_name = os.getenv("S3_BUCKET_NAME")
    bucket = s3.Bucket(bucket_name)

    events = load_events_from_file()

    clear_s3_folder(bucket)

    for event in events:
        create_event_chunk_file(event)
        upload_file_to_s3(bucket, event._id)

    clear_tmp_dir()
    time.sleep(3)
    sync_s3_knowledge_base()

    print(f"\nUploaded {len(events)} events to S3 and synced Bedrock knowledge base.")


def main():
    update_events_file(openai_client)
    fill_db()
    upload_all_events_to_s3()


if __name__ == "__main__":
    start = time.time()
    load_dotenv()
    openai_client = OpenAI()

    main()

    end = time.time()
    print(f"\nFinished in {round((end - start) / 60, 1)} mins.")
