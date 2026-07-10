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
    remove_list = ["15 Wellness Points", "Rise & Roar:", "Mission Ready:", "(All Goodwin Programs)", "(AI)", "()",
                   "@ Drexel University", "@ Drexel U", "@ Drexel", "(ACH)"]
    replace_list = {"Virtual Information Session": "Info Session", "Artificial Intelligence": "AI",
                    "Graduate Student": "Grad Student", "Undergraduate": "Undergrad",
                    "University City Summer Series Concert: Worldtown Soundsystem Collective": "Summer Series Concert: Worldtown Soundsystem Collective"}

    for i in remove_list:
        name = name.replace(i, "", 1)
    for old, new in replace_list.items():
        name = name.replace(old, new, 1)

    return name.strip(" ;/,*").replace("  ", " ")


def simplify_org_name(org_name):
    if not org_name or org_name == "Drexel University":
        return "Drexel University"
    replace_list = {"Drexel P.U.L.S.E: Chapter of Global Public Health Brigades": "P.U.L.S.E",
                    "Undergraduate Student Government Association": "Undergrad Student Gov Association",
                    "Drexel Newman Catholic Community": "Newman Catholic Community",
                    "Drexel Association of Prosthetics and Orthotics": "Association of Prosthetics and Orthotics",
                    "College of Computing and Informatics": "CCI",
                    "Student Academy of the American Academy of Physician Assistants": "American Academy of Physician Assistants",
                    "Elkins Park Student Success & Campus Engagement": "Elkins Park Student Life",
                    "Biomedical Science Graduate Student Association": "Biomed Grad Student Association",
                    "Wilbur W. Oaks Physician Assistant Student Society": "Physician Assistant Student Society",
                    "Hafter Student Community Center": "Hafter Student Center"}
    org_name_remove = ["Drexel Chapter", "Drexel University Chapter", "Drexel Student Chapter",
                       "Drexel University Student Chapter", "Gamma Chapter", "Drexel Section", "at Drexel University",
                       "(CCMADS)", "Shake Team", "&amp", "Philadelphia City Chapter", "at Drexel", "(USGO)",
                       "Incorporated", "Inc.", "Student Group", ", ,"]
    org_name = org_name.strip()

    if org_name in replace_list.keys():
        return replace_list[org_name]
    if org_name.startswith("Drexel University"):
        org_name = org_name.replace("Drexel University", "", 1)
    for i in org_name_remove:
        org_name = org_name.replace(i, "", 1)
    return org_name.strip(":*_;-,. ")


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
                          "Lockheed Martin Launchpad": "Lockheed Martin Launchpad",
                          "Geary Auditorium": "Geary Auditorium", "Mandell Theater": "Mandell Theater",
                          "Drexel Park": "Drexel Park", "Education Abroad Office": "Education Abroad Office",
                          "Academic Building Suite 201": "Education Abroad Office",
                          "Hill Seminar Room": "Hill Seminar Room", "LeBow Eng. 240": "Hill Seminar Room",
                          "Lindy Center for Civic Engagement": "Lindy Center", "The Lindy Center": "Lindy Center",
                          "NSBITT 111": "NSBITT Stein Auditorium", "Stein Auditorium": "NSBITT Stein Auditorium",
                          "NSBITT 125 - Ruth Auditorium": "NSBITT Ruth Auditorium", "Korman Quad": "Korman Quad",
                          "Humpty Dumplings Glenside": "Humpty Dumplings", "The Kimmel Center": "The Kimmel Center",
                          "Penny Park": "Penny Park", "Mitchell Auditorium": "BSONE Mitchell Auditorium",
                          "Penn's Landing": "Penn's Landing",
                          "Cancer Center at the Thomas Jefferson University": "Cancer Center at the Thomas Jefferson University",
                          "URBN Annex Screening Room": "URBN Screening Room",
                          "MAIN - Auditorium": "Main Building Auditorium",
                          "Main Auditorium": "Main Building Auditorium",
                          "Main Auditorium in Main Building": "Main Building Auditorium",
                          "Main Auditorium\r\nMain Building": "Main Building Auditorium",
                          "The Academy of Natural Sciences": "The Academy of Natural Sciences",
                          "The Curtis Atrium": "The Curtis Atrium", "Black Box Theater": "URBN Black Box Theater",
                          "Dornsife Center for Neighborhood Partnership": "Dornsife Center",
                          "Dornsife Center For Neighborhood Partnerships": "Dornsife Center",
                          "3509 Spring Garden St": "Dornsife Center",
                          "Highmark Mann Center": "Highmark Mann Center",
                          "Mack Miles Playground": "Mack Miles Playground",
                          "Office of Graduate Studies": "Office of Graduate Studies",
                          "Office of Graduate Students": "Office of Graduate Studies",
                          "Elkin's Park Parking Lot": "Elkin's Park Parking Lot", "Dragon Statue": "Dragon Statue",
                          "Drexel University Recreation Center": "DAC", "Drexel Recreation Center": "DAC",
                          "Daskalakis Athletic Center": "DAC", "Parkway Central Library": "Parkway Central Library",
                          "Lits Building": "Lits Building", "Independence National Park": "Independence National Park",
                          "3509 Brandywine St & the corner of 36th and Spring Garden": "3509 Brandywine St",
                          "West Philadelphia": "West Philadelphia",
                          "Hafner Community Center": "Hafner Community Center",
                          "Meet in Bentley Hall Lobby at 4:30 or at Asian Arts Initiative (1219 Vine Street) at 5": "Bentley Hall",
                          "Bentley Hall 2nd Floor Annex": "Bentley Hall 2nd Floor",
                          "Tu Rinconcito": "Tu Rinconcito",
                          "Veterans Lounge": "Veterans Lounge", "Academy of Music": "Academy of Music",
                          "New College Building 3rd Floor": "NCB Student Lounge",
                          "Outside Drexel Elkins Park": "Drexel Elkins Park",
                          "CREESE - Greenawalt Room A": "CREESE Room A", "4300 Chester Ave": "Clark Park",
                          "Sunset Social": "Cira Green Rooftop", "Drexel Square": "Drexel Square",
                          "3025 Market St": "Drexel Square", "Babe & Young’s Fashions": "Babe & Young’s Fashions",
                          "110 South 52nd St": "Babe & Young’s Fashions",
                          "Trolley Portal Gardens": "Trolley Portal Gardens",
                          "40th St & Baltimore Avenue": "Trolley Portal Gardens",
                          "PA Arts Gallery": "PA Arts Gallery", "5011 Baltimore Avenue": "PA Arts Gallery"}
    suffixes = [" - Classroom w/ 14 PCs", " - Classroom w/ 6 PCs", " - Classroom w/ 8 PCs", " - COM Classroom",
                " - Classroom", " - Roberta Rosen Sheller Chapel", " - Auditorium", " - Conference",
                "- 1st Floor Exclusive", "(Section 1)", "(2nd Floor)", "(4th Floor)", "(6th Floor)", "(Exclusive)",
                "- All Sections", "- Danzinger Conference Room"]
    remove_list = ["\r", "\r", "\r", "\r", "\n", "\n", "\n", "\n", "In person at the", "In person at", "Pa 19104",
                   "Pa 19103", "Pa 19106", "19103", "19104", "19106", "Philadelphia", "Phila.,", ", PA",
                   "located at the northeast corner of 33rd and Chestnut Streets", "located at 32nd and Market Streets",
                   "101 N 33rd St", "(Main 010 A)", "located at", "3230 Market Street", "- Group Exercise Studio -",
                   "RSVP Required to Attend", "60 N. 36th Street", "33rd and Market Street", ", USA", "(if rain-W106)",
                   "3501 Market Street", "3401 Filbert Street", "3200 Chestnut Street", "3200 Chestnut St",
                   "3141 Chestnut Street", "3141 Chestnut St", "Table Space 1 -", "Table Space 1", "Table Space 2 -",
                   "Table Space 2", "one block north of Market Street", "located at 60 N. 36th Street", " - Class Lab",
                   "3509 Spring Garden St", "60 N 36th St.", "(Exclusive)", "(no specific room)",
                   "3220 Market Street", ", Second Floor", "CNHP Lobby Table", "outside the cafeteria", ]
    replace_list = [(" Streets", " St"), (" Street", " St"), ("\n", " "), ("Philadelphia.", "Philadelphia"),
                    ("N.J.", "NJ"), ("N.J", "NJ"), ("Papadakis Integrated Sciences Building", "PISB"),
                    ("College of Computing & Informatics", "CCI"), ("Creese Student Center", "CREESE"),
                    ("Drexel University Campus", "Drexel Campus"), (" - Alumni Garden", " Garden"),
                    ("Bossone Research and Enterprise Center", "BSONE"), ("Bossone Research Center", "BSONE"),
                    ("Rush building", "RUSH"), ("Rush Building", "RUSH"), ("Gerri C. LeBow Hall", "LEBOW"),
                    ("Pearlstein Business Learning Center", "PEARL"), ("Nesbitt Hall", "NSBITT"),
                    ("Academic Building", "ACADMC"), ("Drexel Health Sciences Building", "HSB"),
                    ("Health Sciences Building", "HSB"), ("Room 209", "RUSH 209"), ("<br>", " "), ("<br>", " "),
                    ("(,", "("), (",)", ")"), (" )", ")"), (" )", ")"), ("()", ""), (" , ", " "), ("  ", " "),
                    ("  ", " "), (" , ", " "), ("  ", " "), ]
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
    for old, new in replace_list:
        location = location.replace(old, new, 1)
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
    s3_subpath = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/images/default_images/"
    name = name.lower() if name else ""
    org_name = org_name.lower() if org_name else ""
    location = location.lower() if location else ""

    pearlstein_image = "https://drexel.edu/news/~/media/Drexel/Core-Site-Group/News/Images/v2/story-images/2022/March/Pearlstein_gallery96-copy/pearlstein_gallery96-copy_16x9.jpg?w=3200&hash=E14D6C3BEF38BF17CAAD5EABC5C9162F"
    westphal_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQejsADyZdJy0QWh6odgCt42Bw9A5fsAPtXMg&s"
    korman_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3qHPfEMM3sZWBAwamvamv8lvT4LzQmfcwQw&s"
    med_building = "https://www.salus.edu/news-stories/_files/images/drexel-nursing-building-pic1.jpg"
    humpty_dumplings = "https://humptysdumplings.com/wp-content/themes/humptysdumplings/images/logo.jpg"
    pisb_image = "https://www.architectmagazine.com/wp-content/uploads/sites/5/2013/616a38fa-c2f8-4e1f-85e3-e23d8bcb9126.jpg"
    rush_building = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/admissions/virtual-tour/rush-building.jpg"
    hagerty_library_image = "https://pbs.twimg.com/media/G8D-sieWQAMOGeO.jpg"
    drexel_default_image = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/home/where-dragons-soar/lancasterwalk-area-lawn-3200x1600_16x9/lancasterwalk-area-lawn-3200x1600_16x9_16x9.jpg"
    dac_image = "https://www.sasaki.com/wp-content/uploads/2019/10/TurDRC09_website-1800x1350.jpg"
    cci_image = "https://stradallc.com/app/uploads/2024/02/DrexelCCI-Lobby2.jpg"
    elkins_park_image = "https://drexel.edu/provost/~/media/Drexel/Provost-Group/Provost/Images/homepage/drexel-elkins-park-campus-4x3.jpg"
    lebow_image = "https://images.squarespace-cdn.com/content/v1/688110841312f04ea8b001bb/7b4c3d88-515e-4315-9776-9390d0e1bd11/LeBow.jpg"
    main_building_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Main_Building_-_Drexel_University_%2853590618820%29.jpg/250px-Main_Building_-_Drexel_University_%2853590618820%29.jpg"

    image_aliases = {"pearlstein gallery": pearlstein_image, "westphal": westphal_image, "dac": dac_image,
                     "rec center": dac_image, "main building": main_building_image, "hagerty": hagerty_library_image,
                     "korman": korman_image, "pisb": pisb_image, "papadakis": pisb_image, "science": pisb_image,
                     "rush": rush_building, "lancaster": drexel_default_image, "nursing": med_building,
                     "medicine": med_building, "humpty dumplings": humpty_dumplings, "cci": cci_image,
                     "elkin": elkins_park_image, "lebow": lebow_image, }
    for key, image in image_aliases.items():
        if key in name or key in org_name or key in location:
            return image
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
    recurring_events = ["board game night", "pizza in the park", "dsc bible study",
                        "graduate fellowships writing group",
                        "tenants' right and organizing", "asl club", "reset lab: a guided mind & body reset",
                        "stay flossy: embroidery workshop", "ucity square beer garden",
                        "food truck thursdays at the lawn",
                        "yoga at ucity square",
                        "university city summer series concert: worldtown soundsystem collective",
                        "creativemornings", "life sciences luncheon", "wellness hub", "open play pickleball",
                        "free health clinic"]
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
    off_campus_orgs = ["Elkins Park Student Life", "Elkins Park Bennett Career Center",
                       "Biomed Grad Student Association", "Elkins Park Student Council"]
    off_campus_locations = ["Elkins Park Cafe", "The Highland Pub & Kitchen", "Humpty Dumplings",
                            "Chipotle Wyncote location", "The Kimmel Center", "Penny Park", "Penn's Landing",
                            "Cancer Center at the Thomas Jefferson University", "Highmark Mann Center",
                            "The Academy of Natural Sciences", "Elkin's Park Parking Lot", "Mack Miles Playground",
                            "Parkway Central Library", "Lits Building", "Independence National Park",
                            "Hafter Center Patio", "Hafner Community Center", "Hafner Student Center", "Haffner Gym"]
    off_campus_keywords = ["england", "new jersey", "maryland", "elkins park", "queen lane", "humpty dumplings",
                           "new college building", "hafner", "hafter", "haffner", "nj"]

    if location in off_campus_locations:
        return False
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
    perk_keywords = {"prizes": "prizes", "15 wellness points": "credit", "giveaway": "giveaway",
                     "free food": "free_food", "free stuff": "free_stuff", "free merch": "free_stuff",
                     "free bling": "free_stuff", "FSL Health & Safety Training": "credit",
                     "we will provide snacks": "free_food", "snacks provided": "free_food", "free scoop": "free_food"}

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

    health_keywords = ["yoga", "zumba", "health", "wellness"]
    academic_keywords = ["academic", "academics", "university", "graduate", "grad school", "graduate school", "webinar",
                         "info session", "molecular medicine", "clinical research"]
    art_keywords = ["arts", "gallery", "exhibit", "museum", "shakespeare", "open mic", "music bingo", "live music",
                    "jazz", "opera", "orchestra", "matinees", "movie", "roland kaiser", "cinéspeak", "film", "theater",
                    "concert", "dance",
                    "late night series", "south african experience", "creativemornings", "fyrestorm"]
    fundraiser_keywords = ["fundraiser", "fundraising", "raise fund"]

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

    return theme


def get_religion(name, org_name, location):
    religious_orgs = {"Chabad Student Group": "jewish", "Jewish Student Association": "jewish",
                      "Drexel Muslim Students Association": "muslim", "Every Nation Campus": "christian",
                      "Drexel Asian Baptist Student Koinonia": "christian", "Story Fellowship": "christian",
                      "Cru": "christian", "Newman Catholic Community": "christian",
                      "Crosswalk Christian Fellowship": "christian", "Christian Fellowship Club": "christian",
                      "Drexel WEH": "christian", "Hindu YUVA @ Drexel": "hindu",
                      "Open Door Christian Community": "christian", "Drexel Students for Christ": "christian"}
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
    excluded_event_names = ["Study Hours", "Ukranian Non-Profit Physical Goods Drive", "Dorm Objects 101",
                            "Visualizing Health: A Photography Exhibit", "Graduate Student Writing Group",
                            "Dorm Objects 101 Guided Tours",
                            "Exploring National Anniversaries Through the Atwater Kent Collection at Drexel",
                            "Recognition Office Hours", "Chapter", "UREP Drop-In Hours",
                            "In Her Own League: The Baseball Collection of Helen Beitler",
                            "Free Uber Rides For Seniors",
                            "Study Abroad Walk-In Hours", "Study Abroad 101",
                            "Intro to Canvas, Drexel's Learning Management System",
                            "West Philadelphia Community Research Review Board", "Creator Studio",
                            "Health Career Exploration Camp", "Revisit 1876",
                            "Lunch & Learn: Improving Interprofessional Communication to Reduce Conflicting Caregiver Guidance",
                            "Graduate Student Resume Drop-Ins", "Graduate Students Resume Drop-Ins",
                            "Fall House Manager Training", "Student Council Meeting",
                            "America’s National Anniversaries & Philadelphia on the World Stage"]
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

    return event


def is_past_max_days_out(event, max_days_out):
    return (event.start_time - datetime.now(tz=event.start_time.tzinfo)).days > max_days_out
