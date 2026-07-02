import copy
import json
from datetime import datetime, timedelta

from backend.python_files.event_class import Event
from backend.python_files.helper_functions import stable_hash


# this is just for weekly static events at local places


def get_static_event_definitions():
    with open("backend/static_recurring_events.json") as f:
        return json.load(f)


def get_weekday_num(weekday_str):
    return {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}[
        weekday_str.lower()]


def find_next_occurrence(weekday_str):
    weekday_num = get_weekday_num(weekday_str)
    now = datetime.today()
    curr_weekday_num = now.weekday()
    days_ahead = weekday_num - curr_weekday_num
    return now + timedelta(days=7 - days_ahead)


def static_event_definition_to_event_object(event_definition):
    date = find_next_occurrence(event_definition["weekday"])

    start_time = datetime.strptime(event_definition["start_time"], "%H:%M").time()
    start = datetime.combine(date, start_time)

    if event_definition["end_time"]:
        end_time = datetime.strptime(event_definition["end_time"], "%H:%M").time()
        end = datetime.combine(date, end_time)
    else:
        end = None

    _id = stable_hash(event_definition["name"] + str(start.timestamp()))

    # todo: implement image parsing

    return Event(
        _id=id,
        source="static_recurring_events",
        name=event_definition["name"],
        org_name=event_definition["org_name"],
        location=event_definition["location"],
        image_url=event_definition["image_url"],
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


def get_instance_of_each_event(event_definitions):
    return [static_event_definition_to_event_object(event_definition) for event_definition in event_definitions]


def get_all_events(weeks_out=4):
    event_definitions = get_static_event_definitions()
    events = get_instance_of_each_event(event_definitions)

    for event in events:
        for i in range(1, weeks_out + 1):
            new_event = copy.deepcopy(event)
            new_event.start_time = event.start_time + timedelta(days=7 * i)
            if event.end_time:
                new_event.end_time = event.end_time + timedelta(days=7 * i)
            new_event._id = stable_hash(new_event.name + str(new_event.start_time.timestamp()))
            events.append(new_event)

    return events
