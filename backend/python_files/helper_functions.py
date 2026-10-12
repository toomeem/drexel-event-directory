import hashlib
import json
import os
from datetime import datetime

from backend.python_files.event_class import Event


def _load_data_file(file_name):
    with open(os.path.join("backend/data_files", file_name), encoding="utf-8") as f:
        return json.load(f)


def stable_hash(key):
    str_bytes = bytes(key, "UTF-8")
    m = hashlib.md5(str_bytes)
    return m.hexdigest()


def normalize_time(time_str):
    if not time_str:
        return None
    dt = datetime.fromisoformat(time_str)
    return dt


def simplify_event_name(name):
    rules = _load_data_file("event_name_simplification.json")

    for k, v in rules["total_replace"].items():
        if k in name:
            return v
    if "Hosted by" in name:
        name = name.split("Hosted by", 1)[0]
    elif "Presents:" in name:
        name = name.split("Presents:", 1)[1]
    elif "Dissertation Defense: " in name:
        name = name.split("Dissertation Defense: ", 1)[0] + "Dissertation Defense"
    for i in rules["remove"]:
        name = name.replace(i, "", 1)
    for old, new in rules["replace"].items():
        name = name.replace(old, new, 1)

    return name.strip(" :;/,*  ").replace("  ", " ")


def simplify_org_name(org_name, event_name, description):
    if org_name == "Drexel University":
        return "Drexel University"

    rules = _load_data_file("org_name_simplification.json")
    if not org_name:
        org_name = ""
    strip_chars = "&:*_;-,.   "
    org_name = org_name.strip(strip_chars)

    if "hosted by in the mix" in event_name.lower() or "hosted by in the mix" in description.lower():
        return "In the Mix"
    elif "Dissertation Defense: " in event_name:
        org_name = event_name.split("Dissertation Defense: ", 1)[1]
    elif "Pétanque Club" in event_name:
        return "Philadelphia Pétanque Club"
    elif org_name in rules["total_replace"]:
        return rules["total_replace"][org_name]
    elif org_name.startswith("Drexel University"):
        org_name = org_name.replace("Drexel University", "", 1)
    for i in rules["remove"]:
        org_name = org_name.replace(i, "", 1)
    for old, new in rules["replace"].items():
        org_name = org_name.replace(old, new, 1)
    if len(org_name.strip(strip_chars)) > 30 and "," in org_name:
        org_name = org_name.split(",", 1)[0]
    return org_name.strip(strip_chars).capitalize()


def simplify_location(location):
    if "cancelled" in location.lower():
        return None
    location = str(location)
    strip_chars = " ,.-*&  "
    rules = _load_data_file("location_simplification.json")

    if "<a href=" in location:
        location = location.split("<a href=", 1)[0]
    for k, v in rules["total_replace"].items():
        if k in location:
            return v
    if "or virtually" in location.lower() or "and virtual" in location.lower():
        location = location.split("or virtually", 1)[0]
    elif "rain location" in location.lower():
        location = location.split("rain location", 1)[0]
    location = location.strip(strip_chars)
    for suffix in rules["suffixes"]:
        location = location.removesuffix(suffix)
    if location.startswith("Philadelphia"):
        return location.replace(", Pa", "").replace("Philadelphia.", "Philadelphia")
    for i in rules["remove"]:
        location = location.replace(i, "", 1)
    for old, new in rules["replace"].items():
        location = location.replace(old, new)
    location = location.strip(strip_chars)

    for i in rules["building_shortnames"]:
        if i in location:
            for old, new in rules["building_shortname_replace"].items():
                location = location.replace(old.replace("{i}", f"{i}"), new.replace("{i}", f"{i}"), 1)
            break
    return location.strip(strip_chars).replace(" , ", " ").replace("  ", " ")  # .capitalize()


def match_default_image(name, org_name, location):
    name, org_name, location = name.lower(), org_name.lower(), location.lower()
    default_images_s3_path = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/images/default_images/"
    image_aliases = _load_data_file("default_image_keyword_list.json")

    for key, image in image_aliases.items():
        if key in name or key in org_name or key in location:
            if image.startswith("s3/"):
                image = default_images_s3_path + image[3:]
            return image

    drexel_default_image = default_images_s3_path + "drexel_default_image.jpg"
    return drexel_default_image


def is_athletic_event(event_name, org_name, location):
    keywords = _load_data_file("athletic_event_rules.json")["keywords"]
    if org_name == "Weekend Warriors":
        return True
    elif org_name == "Dragon Jedi" and "afterclub hangout" not in event_name.lower():
        return True
    elif "vidas" in location.lower():
        return True
    return any(keyword in event_name.lower() for keyword in keywords)


def is_food_related(event_name, perks, location, description):
    rules = _load_data_file("food_event_rules.json")
    if "free_food" in perks:
        return True
    if location in rules["locations"]:
        return True
    event_name = event_name.lower()
    description = description.lower()
    for i in rules["keywords"]:
        if i in event_name or i in description:
            return True
    return False


def is_popular(event_name):
    rules = _load_data_file("popular_event_rules.json")

    if "elkin" in event_name.lower():
        return False

    for keyword in rules["keywords"]:
        if keyword in event_name.lower():
            return True
    return event_name in rules["events"]


def is_recurring(event_name, description):
    rules = _load_data_file("recurring_event_rules.json")
    event_name = event_name.lower()
    description = description.lower()

    for keyword in rules["keywords"]:
        if keyword in event_name or keyword in description:
            return True
    for day_name in rules["day_names"]:
        if day_name + "s" in event_name or day_name + "s" in description:
            return True
        if f"every {day_name}" in event_name or f"every {day_name}" in description:
            return True
    return event_name in rules["events"]


def is_for_new_students(event_name, description):
    rules = _load_data_file("new_student_event_rules.json")
    event_name = event_name.lower()
    description = description.lower()

    for keyword in rules["keywords"]:
        if keyword in event_name or keyword in description:
            return True

    if "undergrad" in event_name and "open house" in event_name:
        return True

    return event_name in [i.lower() for i in rules["events"]]


def is_on_campus(event_name, org_name, location):
    off_campus_keywords = _load_data_file("off_campus_keyword_list.json")
    off_campus_orgs = ["Elkins Park Student Life", "Elkins Park Bennett Career Center",
                       "Biomed Grad Student Association", "Elkins Park Student Council",
                       "Elkins Park Student Engagement & Student Success"]
    on_campus_keywords = ["philly campus", "phl campus", "philadelphia campus"]

    event_name = event_name.lower()
    location = location.lower()
    org_name = org_name.lower()
    for i in on_campus_keywords:
        if i in event_name or i in org_name or i in location:
            return True
    if org_name in off_campus_orgs:
        return False
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
        hybrid_keywords = ["or virtual", "hybrid", "and virtual", "and via Zoom", "and Zoom"]
        for i in hybrid_keywords:
            if i in location.lower():
                return "hybrid"
        return "online"
    else:
        return "in-person"


def enrich_perks(name, description, perks):
    perk_keywords = _load_data_file("perk_keyword_list.json")

    name = name.lower()
    description = description.lower()

    for keyword, perk_type in perk_keywords.items():
        if keyword in name or keyword in description:
            perks.append(perk_type)

    return list(set(perks))


def event_theme_additional_checks(name, description, org_name, location, theme):
    if is_athletic_event(name, org_name, location):
        return "athletics"

    rules = _load_data_file("event_theme_rules.json")
    name = name.lower()
    description = description.lower()

    for keyword in rules["fundraising"]:
        if keyword in name or keyword in description:
            return "fundraising"
    for keyword in rules["health"]:
        if keyword in name or keyword in description:
            return "health"
    for keyword in rules["academic"]:
        if keyword in name or keyword in description:
            return "academic"
    for keyword in rules["art"]:
        if keyword in name or keyword in description:
            return "art"
    for keyword in rules["career"]:
        if keyword in name or keyword in description:
            return "career"

    return theme


def get_religion(name, org_name, location):
    rules = _load_data_file("religion_rules.json")
    if org_name in rules["organizations"]:
        return rules["organizations"][org_name]
    name = name.lower()
    org_name = org_name.lower()
    location = location.lower()
    for keyword in rules["keywords"]:
        if keyword in name or keyword in org_name or keyword in location:
            return rules["keywords"][keyword]
    return None


def is_invalid_event(kwargs):
    rules = _load_data_file("invalid_event_rules.json")

    if kwargs is None:
        return True
    elif not all([kwargs["_id"], kwargs["name"], kwargs["start_time"], kwargs["location"]]):
        return True
    elif kwargs["name"] in rules["event_names"]:
        return True
    elif "cancelled" in kwargs["name"]:
        return True
    elif kwargs["_id"] in rules["ids"]:
        return True
    name = kwargs["name"].lower()
    description = kwargs["description"].lower()
    for i in rules["text"]:
        if i in name or i in description:
            return True
    if kwargs["org_name"]:
        for org in rules["organizations"]:
            if org in kwargs["org_name"]:
                return True
    return False


def clear_directory(path):
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


def create_event_chunk_file(event):
    path = "backend/temp_folders/chunking_tmp_dir/" + event._id + ".json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event.to_chunk_json(), f)


def clear_s3_folder(bucket):
    folder_path = "backend/chunked/"
    bucket.objects.filter(Prefix=folder_path).delete()


def load_events_from_file(path="backend/events.json"):
    with open(path, encoding="utf-8") as f:
        events_json = json.load(f)
    return [Event.from_json(event_json) for event_json in events_json]


def save_events_to_file(events):
    with open("backend/events.json", "w", encoding="utf-8") as f:
        json.dump([event.to_json() for event in events], f, indent=4)


def manual_event_fixes(event):
    # this function may be empty because I will remove code for old events
    match event._id:
        case "0fa765439efaf392c376016f6397cb26":
            event.perks.append("free_stuff")
        case "bd72149c8676d5c78c7a2de5d634b5ee":
            event.perks.append("free_food")
    return event
