import hashlib
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.python_files.event_class import Event
from backend.python_files.lambda_function import make_time_str


def stable_hash(key):
    str_bytes = bytes(key, "UTF-8")
    m = hashlib.md5(str_bytes)
    return m.hexdigest()


def normalize_time(source, time_str):
    if not time_str:
        return None
    if source == "drexel_athletics":
        time_str = time_str.replace("Z", "")
    dt = datetime.fromisoformat(time_str)
    return dt


def simplify_event_name(name):
    remove_list = ["15 Wellness Points", "Rise & Roar:", "Mission Ready:", "(All Goodwin Programs)", "(AI)",
                   "@ Drexel University", "@ Drexel U", "@ Drexel", "(ACH)", "– Spring", "– Summer", "– Fall",
                   "– Winter", "Live at The Lawn:", "at The Lawn", "()", "Movies in Clark Park:",
                   "Zero HIV Stigma Day:", "Stay Flossy:"]
    replace_list = {"Virtual Information Session": "Info Session", "Information Session": "Info Session",
                    "Artificial Intelligence": "AI",
                    "Graduate Student": "Grad Student", "Undergraduate": "Undergrad",
                    "University City Summer Series Concert: Worldtown Soundsystem Collective": "Summer Series Concert: Worldtown Soundsystem Collective",
                    " : ": ": "}
    if "cancelled" in name.lower():
        return None
    if "Hosted by" in name:
        name = name.split("Hosted by", 1)[0]
    elif "Presents:" in name:
        name = name.split("Presents:", 1)[1]
    elif "Dissertation Defense: " in name:
        name = name.split("Dissertation Defense: ", 1)[0] + "Dissertation Defense"
    for i in remove_list:
        name = name.replace(i, "", 1)
    for old, new in replace_list.items():
        name = name.replace(old, new, 1)

    return name.strip(" :;/,*").replace("  ", " ")


def simplify_org_name(org_name, event_name, description):
    if not org_name or org_name == "Drexel University":
        return "Drexel University"
    with open("backend/data_files/org_name_total_replace_list.json") as f:
        total_replace_list = json.load(f)
    org_name_remove = ["Drexel Chapter", "Drexel University Chapter", "Drexel Student Chapter",
                       "Drexel University Student Chapter", "Gamma Chapter", "Drexel Section", "at Drexel University",
                       "(CCMADS)", "Shake Team", "&amp", "Philadelphia City Chapter", "at Drexel", "(USGO)",
                       "Incorporated", "Inc.", "Student Group", ", ,", "& Bulletin Bar"]
    org_name = org_name.strip()

    if "hosted by in the mix" in event_name.lower() or "hosted by in the mix" in description.lower():
        return "In the Mix"
    elif "Dissertation Defense: " in event_name:
        org_name = event_name.split("Dissertation Defense: ", 1)[1]
    elif org_name in total_replace_list.keys():
        return total_replace_list[org_name]
    elif org_name.startswith("Drexel University"):
        org_name = org_name.replace("Drexel University", "", 1)
    for i in org_name_remove:
        org_name = org_name.replace(i, "", 1)
    return org_name.strip("&:*_;-,. ")


def simplify_location(location):
    if "cancelled" in location.lower():
        return None
    location = str(location)
    strip_chars = " ,.-*&"
    with open("backend/data_files/location_total_replace_list.json") as f:
        total_replace_list = json.load(f)
    with open("backend/data_files/location_replace_list.json") as f:
        replace_list = json.load(f)
    with open("backend/data_files/location_remove_list.json") as f:
        remove_list = json.load(f)
    suffixes = [" - Classroom w/ 14 PCs", " - Classroom w/ 6 PCs", " - Classroom w/ 8 PCs", " - COM Classroom",
                " - Classroom", " - Roberta Rosen Sheller Chapel", " - Auditorium", " - Conference",
                "- 1st Floor Exclusive", "(Section 1)", "(2nd Floor)", "(4th Floor)", "(6th Floor)", "(Exclusive)",
                "- All Sections", "- Danzinger Conference Room"]
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
    if location.startswith("Philadelphia"):
        return location.replace(", Pa", "").replace("Philadelphia.", "Philadelphia")
    for i in remove_list:
        location = location.replace(i, "", 1)
    for old, new in replace_list.items():
        location = location.replace(old, new)
    location = location.strip(strip_chars)

    for i in building_shortnames:
        if i in location:
            with open("backend/data_files/building_shortname_replace_list.json") as f:
                location_shortname_simplify_replace_list = json.load(f)
            for old, new in location_shortname_simplify_replace_list.items():
                location = location.replace(old.replace("{i}", f"{i}"), new.replace("{i}", f"{i}"), 1)
            break
    return location.strip(strip_chars).replace(" , ", " ").replace("  ", " ")


def match_default_image(name, org_name, location):
    name, org_name, location = name.lower(), org_name.lower(), location.lower()

    with open("backend/data_files/default_image_keyword_list.json") as f:
        image_aliases = json.load(f)

    for key, image in image_aliases.items():
        if key in name or key in org_name or key in location:
            return image

    drexel_default_image = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/home/where-dragons-soar/lancasterwalk-area-lawn-3200x1600_16x9/lancasterwalk-area-lawn-3200x1600_16x9_16x9.jpg"
    return drexel_default_image


def is_athletic_event(event_name, org_name, location):
    athletics_keywords = ["pilates", "bhangra", "salsa", "spikeball", "spike ball",
                          "kayaking", "paintball", "hike", "hiking", "skiing",
                          "snowboarding", "rafting", "horseback riding", "paddleboarding", "canoeing", "canoe",
                          "surfing", "scuba", "biking", "dance workshop", "dance class", "sumo night"]
    if org_name == "Weekend Warriors":
        return True
    elif org_name == "Dragon Jedi" and "afterclub hangout" not in event_name.lower():
        return True
    elif "vidas" in location.lower():
        return True
    return any([keyword in event_name.lower() for keyword in athletics_keywords])


def is_food_related(event_name, perks, location, description):
    food_locations = ["Elkins Park Cafe", "The Highland Pub & Kitchen", "Humpty Dumplings", "Chipotle Wyncote location"]
    food_keywords = ["food", "coffee", "bake sale", "lemonade stand", "chipotle", "bbq", "ice cream", "pizza", "snacks",
                     "breakfast", "lunch", "dinner", "refreshments" "coffee", "beer", "wine", "cocktails", "meal",
                     "cookout", "water ice"]
    if "free_food" in perks:
        return True
    if location in food_locations:
        return True
    event_name = event_name.lower()
    description = description.lower()
    for i in food_keywords:
        if i in event_name or i in description:
            return True
    return False


def is_popular(event_name):
    popular_events = ["Lawn Games", "Summer Bash BBQ", "Free Cone & Free Speech", "Game Night",
                      "Future Dragons Breakfast", "Snow Cone Social",
                      "Field Trip: Art and Community Protest at the Asian Arts Initiative", "Nerd Night",
                      "Undergrad July Summer Open House",
                      "STAR Scholars Summer Showcase", "Welcome Week: Night on the Row 2026"
                      ]
    if "welcome week" in event_name.lower():
        return True
    return event_name in popular_events


def is_recurring(event_name, description):
    with open("backend/data_files/dynamic_recurring_event_list.json") as f:
        recurring_events = json.load(f)
    day_names = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    recurring_keywords = ["recurring", "monthly", "weekly", "series", "weeklies"]
    event_name = event_name.lower()
    description = description.lower()

    for keyword in recurring_keywords:
        if keyword in event_name or keyword in description:
            return True
    for day_name in day_names:
        if day_name + "s" in event_name or day_name + "s" in description:
            return True
        if f"every {day_name}" in event_name or f"every {day_name}" in description:
            return True
    return event_name in recurring_events


def is_for_new_students(event_name, description):
    new_student_events = ["Undergrad July Summer Open House",
                          "Field Trip: Art and Community Protest at the Asian Arts Initiative"]
    event_name = event_name.lower()
    description = description.lower()
    keywords = ["new student", "future dragons", "incoming freshman", "welcome week"]

    for keyword in keywords:
        if keyword in event_name or keyword in description:
            return True

    if "undergrad" in event_name and "open house" in event_name:
        return True

    return event_name in [i.lower() for i in new_student_events]


def is_on_campus(event_name, org_name, location):
    with open("backend/data_files/off_campus_keyword_list.json") as f:
        off_campus_keywords = json.load(f)
    off_campus_orgs = ["Elkins Park Student Life", "Elkins Park Bennett Career Center",
                       "Biomed Grad Student Association", "Elkins Park Student Council"]

    if org_name in off_campus_orgs:
        return False

    event_name = event_name.lower()
    location = location.lower()
    for i in off_campus_keywords:
        if i in event_name or i in org_name or i in location:
            return False

    return True


def get_event_status(source, location):
    online_keywords = ["zoom", "virtual", "hybrid", "handshake", "online", "remote"]
    online_location_default_text = ["Online", "Zoom (Link in description)", "Zoom",
                                    "Virtual - see reminder email for link", "Online Event", "Remote",
                                    "Zoom: Register on Handshake"]
    if source == "drexel_athletics":
        return "in-person"
    elif location in online_location_default_text:
        return "online"
    elif any(keyword in location.lower() for keyword in online_keywords):
        hybrid_keywords = ["or virtual", "hybrid", "and virtual", "and via Zoom"]
        for i in hybrid_keywords:
            if i in location.lower():
                return "hybrid"
        return "online"
    else:
        return "in-person"


def enrich_perks(name, description, perks):
    with open("backend/data_files/perk_keyword_list.json") as f:
        perk_keywords = json.load(f)

    name = name.lower()
    description = description.lower()

    for keyword, perk_type in perk_keywords.items():
        if keyword in name or keyword in description:
            perks.append(perk_type)

    return list(set(perks))


def event_theme_additional_checks(name, description, org_name, location, theme):
    if is_athletic_event(name, org_name, location):
        return "athletics"

    name = name.lower()
    description = description.lower()

    health_keywords = ["yoga", "zumba", "health", "wellness", "reset lab"]
    academic_keywords = ["academic", "academics", "university", "graduate", "grad school", "graduate school", "webinar",
                         "info session", "molecular medicine", "clinical research", "life sciences"]
    art_keywords = ["arts", "gallery", "exhibit", "museum", "shakespeare", "open mic", "music bingo", "live music",
                    "jazz", "opera", "orchestra", "matinees", "movie", "roland kaiser", "cinéspeak", "film", "theater",
                    "concert", "dance", "embroidery", "asl", "late night series", "south african experience",
                    "creativemornings", "fyrestorm"]
    fundraiser_keywords = ["fundraiser", "fundraising", "raise fund"]
    career_keywords = ["career", "innovation exchange", "retention by design"]

    for keyword in fundraiser_keywords:
        if keyword in name or keyword in description:
            return "fundraising"
    for keyword in health_keywords:
        if keyword in name or keyword in description:
            return "health"
    for keyword in academic_keywords:
        if keyword in name or keyword in description:
            return "academic"
    for keyword in art_keywords:
        if keyword in name or keyword in description:
            return "art"
    for keyword in career_keywords:
        if keyword in name or keyword in description:
            return "career"

    return theme


def get_religion(name, org_name, location):
    with open("backend/data_files/religious_org_list.json") as f:
        religious_orgs = json.load(f)
    religious_keywords = {"church": "christian", "methodist": "christian", "synagogue": "jewish"}
    if org_name in religious_orgs.keys():
        return religious_orgs[org_name]
    name = name.lower()
    org_name = org_name.lower()
    location = location.lower()
    for keyword in religious_keywords.keys():
        if keyword in name or keyword in org_name or keyword in location:
            return religious_keywords[keyword]
    return None


def invalid_event(kwargs):
    with open("backend/data_files/excluded_event_names.json") as f:
        excluded_event_names = json.load(f)
    excluded_event_ids = ["d0b6c726f28fb1f105d6df9c02797617"]

    if kwargs is None:
        return True
    elif not all([kwargs["_id"], kwargs["name"], kwargs["start_time"], kwargs["location"]]):
        return True
    elif kwargs["name"] in excluded_event_names:
        return True
    elif kwargs["name"].startswith("CANCELLED"):
        return True
    elif kwargs["_id"] in excluded_event_ids:
        return True
    name = kwargs["name"].lower()
    general_body_meeting_keywords = ["general body meeting", "gbm", "chapter meeting", "presidents meeting",
                                     "e-board meeting", "officer meeting", "exec board"]
    for keyword in general_body_meeting_keywords:
        if keyword in name:
            return True
    return False


def clear_directory(path):
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


def create_event_chunk_file(event):
    path = "backend/temp_folders/chunking_tmp_dir/" + event._id + ".json"
    event_json = event.to_json()
    event_json["formatted_time_str"] = make_time_str(event.start_time, event.end_time)
    del event_json["event_link"]
    del event_json["image_url"]
    del event_json["id"]
    del event_json["start_time"]
    del event_json["end_time"]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(event_json, f)


def clear_s3_folder(bucket):
    folder_path = "backend/chunked/"
    bucket.objects.filter(Prefix=folder_path).delete()


def load_events_from_file(path="backend/events.json"):
    with open(path, encoding="utf-8") as f:
        events_json = json.load(f)
    events = []
    for e in events_json:
        events.append(
            Event(_id=e["id"], source=e["source"], name=e["name"], org_name=e["org_name"], location=e["location"],
                  image_url=e["image_url"],
                  start_time=datetime.fromtimestamp(e["start_time"]) if e["start_time"] else None,
                  end_time=datetime.fromtimestamp(e["end_time"]) if e["end_time"] else None, event_link=e["event_link"],
                  event_status=e["event_status"], theme=e["theme"], perks=e["perks"], food_related=e["food_related"],
                  popular=e["popular"], recurring=e["recurring"], for_new_students=e["for_new_students"],
                  on_campus=e["on_campus"], religion=e["religion"]))
    return events


def save_events_to_file(events):
    with open("backend/events.json", "w", encoding="utf-8") as f:
        json.dump([event.to_json() for event in events], f, indent=4)


def manual_event_fixes(event):
    match event._id:
        case "7dcb5b09133454510007247120737074":
            PHILLY_TZ = ZoneInfo("America/New_York")
            event.end_time = datetime(2026, 7, 18, 13).astimezone(PHILLY_TZ)
        case "22a66ff543a693b1d383744c3f715f5e":
            event.org_name = event.name
        case "c63a185e9635dee8d40ae36fdedb20c9":
            event.location = "Lanc Ave & 33rd -> Market St & 2nd"

    return event


def is_past_max_days_out(event, max_days_out):
    return (event.start_time - datetime.now(tz=event.start_time.tzinfo)).days > max_days_out
