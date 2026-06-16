import hashlib
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from pydantic import BaseModel

import requests
from backend.python_files.event_class import Event

PHILLY_TZ = ZoneInfo("America/New_York")
HTTP_TIMEOUT = (5, 30)


class OnlineStatus(BaseModel):
    event_status: str  # in-person, virtual, hybrid
    physical_location: str


def stable_hash(key):
    str_bytes = bytes(key, "UTF-8")
    m = hashlib.md5(str_bytes)
    print(m.hexdigest())
    return m.hexdigest()


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
    if "cancelled" in location.lower():
        return None
    location = str(location)
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
                          "Elkin's Park Parking Lot": "Elkin's Park Parking Lot", "Dragon Statue": "Dragon Statue",
                          "Drexel University Recreation Center": "DAC", "Drexel Recreation Center": "DAC",
                          "Daskalakis Athletic Center": "DAC", "Parkway Central Library": "Parkway Central Library",
                          "Lits Building": "Lits Building", "Independence National Park": "Independence National Park",
                          "3509 Brandywine St & the corner of 36th and Spring Garden": "3509 Brandywine St"}
    suffixes = [" - Classroom w/ 14 PCs", " - Classroom w/ 6 PCs", " - Classroom w/ 8 PCs", " - COM Classroom",
                " - Classroom", " - Roberta Rosen Sheller Chapel", " - Auditorium", " - Conference",
                "- 1st Floor Exclusive", "(Section 1)", "(2nd Floor)", "(4th Floor)", "(6th Floor)", "(Exclusive)",
                "- All Sections", "- Danzinger Conference Room"]
    remove_list = ["\r", "\r", "\r", "\r", "\n", "\n", "\n", "\n", "In person at the", "In person at", "Pa 19104",
                   "Pa 19103", "Pa 19106", "19103", "19104", "19106", "Philadelphia", ", PA",
                   "located at the northeast corner of 33rd and Chestnut Streets", "located at 32nd and Market Streets",
                   "101 N 33rd St", "(Main 010 A)", "located at", "3230 Market Street", "- Group Exercise Studio -",
                   "RSVP Required to Attend", "60 N. 36th Street", "33rd and Market Street", ", USA", "(if rain-W106)",
                   "3501 Market Street", "3401 Filbert Street", "3200 Chestnut Street", "3200 Chestnut St",
                   "3141 Chestnut Street", "3141 Chestnut St", "Table Space 1 -", "Table Space 1", "Table Space 2 -",
                   "Table Space 2", "one block north of Market Street", "located at 60 N. 36th Street", " - Class Lab",
                   "3509 Spring Garden St", "60 N 36th St.", "3675 Market Street", "(Exclusive)", "(no specific room)"]
    replace_list = [(" Streets", " St"), (" Street", " St"), ("\n", " "),
                    ("Papadakis Integrated Sciences Building", "PISB"), ("College of Computing & Informatics", "CCI"),
                    ("Creese Student Center", "CREESE"), ("Drexel University Campus", "Drexel Campus"),
                    ("Bossone Research and Enterprise Center", "BSONE"), ("Bossone Research Center", "BSONE"),
                    ("Rush building", "RUSH"), ("Rush Building", "RUSH"), (" - Alumni Garden", " Garden"),
                    ("Pearlstein Business Learning Center", "PEARL"), ("Nesbitt Hall", "NSBITT"),
                    ("Academic Building", "ACADMC"), ("Gerri C. LeBow Hall", "LEBOW"),
                    ("Drexel Health Sciences Building", "HSB"), ("Health Sciences Building", "HSB"),
                    ("Room 209", "RUSH 209"), ("(,", "("), (",)", ")"), (" )", ")"), (" )", ")"), ("()", ""),
                    (" , ", " "), ("  ", " "), ("  ", " "), (" , ", " "), ("  ", " "), ]
    building_shortnames = ["PISB", "CREESE", "BSONE", "RUSH", "ACADMC", "RANDEL", "RANDELL", "GHALL", "MAIN", "URBN",
                           "URBN", "PEARL", "CAT", "NSBITT", "Korman", "HSB", "ROSS", "LEBOW", "LeBow", "JEMIC", "CCI",
                           "DAC"]

    for k, v in total_replace_list.items():
        if k in location:
            return v
    if "or virtually" in location.lower() or "and virtual" in location.lower():
        location = location.split("or virtually", 1)[0]
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
            location = location.replace(f"({i})", "", 1).replace(f"{i} Center", f"{i} ", 1).replace(f"{i} center",
                                                                                                    f"{i} ", 1)
            location = (
                location.replace(f"{i}, Room", f"{i} ", 1).replace(f"{i}, room", f"{i} ", 1).replace(f"{i} - Room",
                                                                                                     f"{i} ",
                                                                                                     1).replace(
                    f"{i} - room", f"{i} ", 1).replace(f"{i} Room", f"{i} ", 1).replace(f"{i} room", f"{i} ",
                                                                                        1).replace(f"{i}Room", i,
                                                                                                   1).replace(
                    f"{i}room", f"{i} ", 1).replace(f"{i} Suite", f"{i} ", 1).replace(f"{i} Meeting room", f"{i} ",
                                                                                      1).replace(f"{i} Meeting Room",
                                                                                                 i).replace(
                    f"{i} meeting room", f"{i} ", 1).replace(f"{i},", f"{i} ", 1)).replace(f"{i}Suite", f"{i} ",
                                                                                           1).replace(f"{i}Room",
                                                                                                      f"{i} ",
                                                                                                      1).replace(
                f"{i}room", f"{i} ", 1)
            break
    return location.strip(strip_chars).replace(" , ", " ").replace("  ", " ").replace("  ", " ")


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


def dragonlink_event_parsing(event_json, kwargs):
    source = "dragonlink"
    dragonlink_base_url = "https://drexel.campuslabs.com/engage/"
    dragonlink_image_url = dragonlink_base_url + "image/"
    dragonlink_event_url = dragonlink_base_url + "event/"
    specific_events_to_exclude = ["12449523", "12449521"]

    if str(event_json["id"]) in specific_events_to_exclude:
        return None
    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
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

    if "General Body Meeting" in event_json["categoryNames"] or "Presidents Meeting" in event_json["categoryNames"]:
        return None
    elif kwargs["org_name"] in religious_orgs:
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

    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
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

    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
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
    online_location_default_text = ["Online", "Zoom (Link in description)", "Zoom",
                                    "Virtual - see reminder email for link", "Online Event", "Remote",
                                    "Zoom: Register on Handshake"]
    exclude_events = ["Drexel FSAE Sping GBM 2025", "Study Hours", "Drexel University Circle K General Body Meeting",
                      "Ukranian Non-Profit Physical Goods Drive", "Dorm Objects 101",
                      "Visualizing Health: A Photography Exhibit", "Graduate Student Writing Group",
                      "Dorm Objects 101 Guided Tours", "GBM #5",
                      "Exploring National Anniversaries Through the Atwater Kent Collection at Drexel",
                      "Recognition Office Hours", "Chapter", "UREP Drop-In Hours", "SASE Spring Term E-board Meetings",
                      "SWE Spring 2026 Officer Meetings", "In Her Own League: The Baseball Collection of Helen Beitler"]
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
            kwargs["name"].lower() or "Chpater" in kwargs["name"]:
        return None
    if kwargs["name"].startswith("CANCELLED"):
        return None
    kwargs["name"] = kwargs["name"].replace("(15 Wellness Points)", "").strip(" ;:/,*")
    if kwargs["image_url"] is None:
        kwargs["image_url"] = match_default_image(kwargs["name"], kwargs["org_name"], kwargs["location"])

    if source == "drexel_athletics":
        kwargs["event_status"] = "in-person"
    elif kwargs["location"] in online_location_default_text:
        kwargs["event_status"] = "virtual"
    elif any(keyword in kwargs["location"].lower() for keyword in online_keywords):
        hybrid_keywords = ["or virtual", "hybrid", "and virtual", "and via Zoom"]
        for i in hybrid_keywords:
            if i in kwargs["location"].lower():
                kwargs["event_status"] = "hybrid"
                break
            else:
                kwargs["event_status"] = "virtual"
    else:
        kwargs["event_status"] = "in-person"

    if kwargs["event_status"] == "virtual":
        kwargs["location"] = "Online"
    else:
        kwargs["location"] = simplify_location(kwargs["location"])
    if kwargs["location"] is None:
        return None

    org_name_remove = ["Drexel Chapter", "Drexel University Chapter", "Drexel Student Chapter",
                       "Drexel University Student Chapter", "Gamma Chapter", "Drexel Section", "at Drexel University",
                       "(CCMADS)", "Shake Team", "&amp", "Philadelphia City Chapter", "at Drexel", "(USGO)",
                       "Incorporated", "Inc.", "Student Group", ", ,"]
    if kwargs["org_name"].startswith("Drexel University"):
        kwargs["org_name"] = kwargs["org_name"].replace("Drexel University", "", 1)
    for i in org_name_remove:
        kwargs["org_name"] = kwargs["org_name"].replace(i, "", 1)
    kwargs["org_name"] = kwargs["org_name"].strip(";-,. ")
    # todo: remove "Drexel " prefix from org names with a few exceptions
    return Event(**kwargs)


def create_dragonlink_api_url(count):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
    base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
    return base_url + "?endsAfter=" + timestamp + base_filters + str(count)


def collect_dragonlink_events(count=300):
    response = requests.get(create_dragonlink_api_url(count), timeout=HTTP_TIMEOUT)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []

    response = dict(response.json())
    os.makedirs("json_examples", exist_ok=True)
    with open("backend/json_examples/dragonlink_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4)

    return response["value"]


def create_drexel_events_api_url(page=1):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def get_drexel_events_response(page):
    time.sleep(random.random() * 0.5)
    response = requests.get(create_drexel_events_api_url(page), timeout=HTTP_TIMEOUT)
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []
    return dict(response.json())["results"]


def collect_drexel_events(count=200):
    results = []
    events_per_page = 10
    max_threads = 5
    total_requests = (count // events_per_page) + 1
    requests_nums = [i for i in range(1, total_requests + 1)]

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(get_drexel_events_response, i) for i in requests_nums]
        for future in as_completed(futures):
            results.extend(future.result())

    os.makedirs("json_examples", exist_ok=True)
    with open("backend/json_examples/drexel_events_response.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    return results


def create_drexel_athletics_api_url(days_out=30):
    # set default days_out to higher amount after streamlining data collection process
    now = datetime.now()
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def collect_drexel_athletics_events():
    url = create_drexel_athletics_api_url()
    response = requests.get(url, timeout=HTTP_TIMEOUT)

    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []

    response_json = list(response.json())
    events_json = []

    for day in response_json:
        if day["events"] is None:
            continue
        for event in day["events"]:
            events_json.append(event)

    os.makedirs("json_examples", exist_ok=True)
    with open("backend/json_examples/drexel_athletics_response.json", "w", encoding="utf-8") as f:
        json.dump(events_json, f, indent=4)

    return events_json
