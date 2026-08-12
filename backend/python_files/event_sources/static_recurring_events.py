import json
from copy import deepcopy
from datetime import datetime, timedelta

from backend.python_files.event_class import Event
from backend.python_files.helper_functions import stable_hash
from backend.python_files.image_parsing_functions import get_image_s3_url


# this is just for weekly static events at local places


def get_static_event_definitions():
    with open("backend/data_files/static_recurring_events.json") as f:
        return json.load(f)


def get_weekday_num(weekday_str):
    return {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}[
        weekday_str.lower()]


def find_next_occurrence(weekday_str):
    weekday_num = get_weekday_num(weekday_str)
    now = datetime.today()
    while now.weekday() != weekday_num:
        now += timedelta(days=1)
    return now


def static_event_definition_to_event_object(event_definition, bucket_name):
    date = find_next_occurrence(event_definition["weekday"])

    start_time = datetime.strptime(event_definition["start_time"], "%H:%M").time()
    start = datetime.combine(date, start_time)

    if event_definition["end_time"]:
        end_time = datetime.strptime(event_definition["end_time"], "%H:%M").time()
        end = datetime.combine(date, end_time)
    else:
        end = None

    id = stable_hash(event_definition["name"] + str(start.timestamp()))
    image_url = get_image_s3_url(event_definition["image_url"], bucket_name)

    return Event(
        _id=id,
        source="static_recurring_events",
        name=event_definition["name"],
        org_name=event_definition["org_name"],
        location=event_definition["location"],
        image_url=image_url,
        start_time=start,
        end_time=end if end else None,
        event_link=event_definition["event_link"],
        event_status=event_definition["event_status"],
        theme=event_definition["theme"],
        perks=event_definition["perks"],
        food_related=event_definition["food_related"],
        popular=event_definition["popular"],
        recurring=True,
        for_new_students=event_definition["for_new_students"],
        on_campus=True,
        religion=None
    )


def get_instance_of_each_event(event_definitions, bucket_name):
    return [static_event_definition_to_event_object(event_definition, bucket_name) for event_definition in
            event_definitions]


def get_static_events(bucket_name, existing_event_ids, occurrences=4):
    event_definitions = get_static_event_definitions()
    original_events = get_instance_of_each_event(event_definitions, bucket_name)

    all_events = []
    for original_event in original_events:
        all_events.append(original_event)
        for i in range(1, occurrences):
            new_event = deepcopy(original_event)

            new_event.start_time = original_event.start_time + timedelta(days=7 * i)
            if original_event.end_time:
                new_event.end_time = original_event.end_time + timedelta(days=7 * i)
            new_event._id = stable_hash(new_event.name + str(new_event.start_time.timestamp()))

            all_events.append(new_event)

    event_json_list = []
    for event in all_events:
        if event._id not in existing_event_ids:
            event_json = event.to_json()
            event_json["_id"] = event_json.pop("id")
            event_json["description"] = ""
            event_json["start_time"] = datetime.fromtimestamp(event_json["start_time"])
            if event_json["end_time"]:
                event_json["end_time"] = datetime.fromtimestamp(event_json["end_time"])
            event_json_list.append(event_json)

    return event_json_list
