import os
import time
from datetime import timezone

import pg8000.dbapi

import boto3
from backend.python_files.event_class import Event
from backend.python_files.event_sources.bbj_events import bbj_event_parsing, get_bbj_events
from backend.python_files.event_sources.dragonlink_event_functions import collect_dragonlink_events, \
    dragonlink_event_parsing
from backend.python_files.event_sources.drexel_athletics_event_functions import collect_drexel_athletics_events, \
    drexel_athletics_event_parsing
from backend.python_files.event_sources.drexel_event_functions import collect_drexel_events, drexel_event_parsing
from backend.python_files.event_sources.ucity_district_events import ucity_district_event_parsing, \
    collect_ucity_district_events
from backend.python_files.event_sources.ucity_square_event_functions import get_all_ucity_square_urls, \
    create_ucity_square_event_from_url, get_ucity_square_event_data
from backend.python_files.helper_functions import invalid_event, simplify_org_name, get_event_status, \
    match_default_image, simplify_location, is_food_related, is_popular, is_recurring, is_for_new_students, \
    is_on_campus, clear_directory, create_event_chunk_file, load_events_from_file, save_events_to_file, \
    manual_event_fixes, simplify_event_name, enrich_perks, event_theme_additional_checks, get_religion, \
    is_past_max_days_out
from backend.python_files.image_parsing_functions import get_image_s3_url
from dotenv import load_dotenv


def simple_events_in_db():
    conn = pg8000.dbapi.connect(host=os.getenv("RDS_ENDPOINT"), database="postgres", user=os.getenv("RDS_USERNAME"),
                                password=os.getenv("RDS_PASSWORD"), port=5432, ssl_context=True)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name, source, org_name, start_time FROM main.events")
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


def get_events_from_db():
    events = []
    event_data = simple_events_in_db()
    for row in event_data:
        # The start_time column is "timestamp without time zone" stored in UTC, so
        # pg8000 returns a naive datetime. Mark it as UTC-aware, otherwise
        # get_start_timestamp() would reinterpret it in the local zone and shift the
        # epoch by the local UTC offset, breaking equality checks against new events.
        start_time = row[4].replace(tzinfo=timezone.utc)
        event = Event(
            _id=row[0],
            source=row[2],
            name=row[1],
            org_name=row[3],
            start_time=start_time,
            location=None,
            end_time=None,
            image_url=None,
            event_link=None,
            event_status=None,
            theme=None,
            perks=None,
            food_related=False,
            popular=False,
            recurring=False,
            for_new_students=False,
            on_campus=True,
            religion=None
        )
        events.append(event)
    return events


def create_event_object(source, event_data, bucket_name, existing_event_ids):
    kwargs = {"_id": None, "source": source, "name": None, "org_name": None, "location": None, "image_url": None,
              "start_time": None, "end_time": None, "event_link": None, "event_status": None, "theme": None,
              "perks": [], "food_related": False, "popular": False, "recurring": False, "for_new_students": False,
              "on_campus": True, "religion": None, "description": ""}

    match source:
        case "dragonlink":
            kwargs = dragonlink_event_parsing(event_data, kwargs, existing_event_ids)
        case "drexel_events":
            kwargs = drexel_event_parsing(event_data, kwargs, existing_event_ids)
        case "drexel_athletics":
            kwargs = drexel_athletics_event_parsing(event_data, kwargs, existing_event_ids)
        case "ucity_square":
            kwargs = create_ucity_square_event_from_url(event_data, kwargs, existing_event_ids)
        case "ucity_district":
            kwargs = ucity_district_event_parsing(event_data, kwargs, existing_event_ids)
        case "bbj":
            kwargs = bbj_event_parsing(event_data, kwargs, existing_event_ids)
        case _:
            return None
    if invalid_event(kwargs):
        return None

    kwargs["perks"] = enrich_perks(kwargs["name"], kwargs["description"], kwargs["perks"])
    kwargs["name"] = simplify_event_name(kwargs["name"])
    kwargs["org_name"] = simplify_org_name(kwargs["org_name"])
    kwargs["event_status"] = get_event_status(source, kwargs["location"])

    if kwargs["image_url"] is None:
        kwargs["image_url"] = get_image_s3_url(
            match_default_image(kwargs["name"], kwargs["org_name"], kwargs["location"]), bucket_name)
    else:
        kwargs["image_url"] = get_image_s3_url(kwargs["image_url"], bucket_name)
        if kwargs["image_url"] is None:
            kwargs["image_url"] = get_image_s3_url(
                match_default_image(kwargs["name"], kwargs["org_name"], kwargs["location"]), bucket_name)

    if kwargs["event_status"] == "online":
        kwargs["location"] = "Online"
    else:
        kwargs["location"] = simplify_location(kwargs["location"])
        if kwargs["location"] is None:
            return None

    kwargs["food_related"] = is_food_related(kwargs["name"], kwargs["perks"], kwargs["location"], kwargs["description"])
    kwargs["popular"] = is_popular(kwargs["name"])
    kwargs["recurring"] = is_recurring(kwargs["name"], kwargs["description"])
    kwargs["for_new_students"] = is_for_new_students(kwargs["name"], kwargs["description"])
    kwargs["on_campus"] = is_on_campus(kwargs["name"], kwargs["org_name"], kwargs["location"])
    kwargs["religion"] = get_religion(kwargs["name"], kwargs["org_name"], kwargs["location"])
    if kwargs["religion"]:
        kwargs["theme"] = "spirituality"
    else:
        kwargs["theme"] = event_theme_additional_checks(kwargs["name"], kwargs["description"],
                                                        kwargs["org_name"], kwargs["location"], kwargs["theme"])

    del kwargs["description"]
    return Event(**kwargs)


def collect_and_parse_all_dragonlink_events(bucket_name, existing_event_ids, count):
    events = []
    for event_json in collect_dragonlink_events(count):
        event = create_event_object("dragonlink", event_json, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def collect_and_parse_all_drexel_events(bucket_name, existing_event_ids, count):
    events = []
    for event_json in collect_drexel_events(count):
        event = create_event_object("drexel_events", event_json, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def collect_and_parse_all_drexel_athletics_events(bucket_name, existing_event_ids, days_out):
    events = []
    for event_json in collect_drexel_athletics_events(days_out):
        event = create_event_object("drexel_athletics", event_json, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def collect_and_parse_all_ucity_square_events(bucket_name, existing_event_ids, months_out):
    events = []
    for event_url in get_all_ucity_square_urls(months_out):
        event_data = get_ucity_square_event_data(event_url)
        event = create_event_object("ucity_square", event_data, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def collect_and_parse_all_ucity_district_events(bucket_name, existing_event_ids, count):
    events = []
    for event_json in collect_ucity_district_events(count):
        event = create_event_object("ucity_district", event_json, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def collect_and_parse_all_bbj_events(bucket_name, existing_event_ids):
    events = []
    for event_json in get_bbj_events():
        event = create_event_object("bbj", event_json, bucket_name, existing_event_ids)
        if event is not None:
            events.append(event)
    return events


def dedup_events(events_in_db, events):
    source_priority = {"drexel_events": 0, "drexel_athletics": 1, "dragonlink": 2, "ucity_square": 3,
                       "ucity_district": 4, "other": 5, }

    # group possible duplicates by start time first
    events_by_start = {}
    for e in events:
        events_by_start.setdefault(e.start_time.timestamp(), []).append(e)

    result = []
    for candidates in events_by_start.values():
        clusters = []
        for event in candidates:
            if event in events_in_db:
                continue
            for cluster in clusters:
                if any(event == existing for existing in cluster):
                    cluster.append(event)
                    break
            else:
                clusters.append([event])

        for cluster in clusters:
            result.append(max(cluster, key=lambda e: source_priority.get(e.source, -1)))

    result.sort(key=lambda e: e.start_time.timestamp())
    return result


def collect_all_events(bucket_name, events_in_db, days_out):
    existing_event_ids = [i._id for i in events_in_db]
    events = []
    #
    # events.extend(collect_and_parse_all_ucity_square_events(bucket_name, existing_event_ids, months_out=2))
    # event_count = len(events)
    # print(f"\nCollected {event_count} UCity Square events.")
    #
    # events.extend(collect_and_parse_all_dragonlink_events(bucket_name, existing_event_ids, count=350))
    # print(f"Collected {len(events) - event_count} Dragonlink events.")
    # event_count = len(events)
    #
    # events.extend(collect_and_parse_all_drexel_events(bucket_name, existing_event_ids, count=350))
    # print(f"Collected {len(events) - event_count} Drexel events.")
    # event_count = len(events)
    #
    events.extend(collect_and_parse_all_drexel_athletics_events(bucket_name, [], days_out=days_out))
    # print(f"Collected {len(events) - event_count} Drexel Athletics events.")
    # event_count = len(events)
    #
    # events.extend(collect_and_parse_all_ucity_district_events(bucket_name, existing_event_ids, count=500))
    # print(f"Collected {len(events) - event_count} uCity District events.")
    # event_count = len(events)
    #
    # events.extend(get_static_events(bucket_name, occurrences=6))
    # print(f"Added {len(events) - event_count} static events.")
    # event_count = len(events)
    #
    # events.extend(collect_and_parse_all_bbj_events(bucket_name, existing_event_ids))
    # print(f"Added {len(events) - event_count} Black Bottom Jazz events.")
    #
    events = [i for i in events if not is_past_max_days_out(i, days_out)]
    events = [manual_event_fixes(event) for event in events]
    events = dedup_events(events_in_db, events)

    return events


def update_events_file(bucket_name, days_out):
    print("\nCollecting events...")

    db_events = get_events_from_db()
    events = collect_all_events(bucket_name, db_events, days_out)
    save_events_to_file(events)
    print(f"\nSaved {len(events)} events to file.")


def save_events_to_db(events):
    event_rows_by_id = {}
    for event in events:
        event_row = event.to_sql()
        event_rows_by_id.setdefault(event_row[0], event_row)

    if not event_rows_by_id:
        return 0

    conn = pg8000.dbapi.connect(host=os.getenv("RDS_ENDPOINT"), database="postgres", user=os.getenv("RDS_USERNAME"),
                                password=os.getenv("RDS_PASSWORD"), port=5432, ssl_context=True)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM main.events WHERE id = ANY(%s)", (list(event_rows_by_id.keys()),))
            existing_event_ids = {row[0] for row in cursor.fetchall()}
            new_event_rows = [row for event_id, row in event_rows_by_id.items() if event_id not in existing_event_ids]

            if not new_event_rows:
                return 0

            cursor.executemany('''
                               INSERT INTO main.events(id, source, name, org_name, location, image_url, start_time,
                                                       end_time,
                                                       event_link, event_status, theme, perks, food_related, popular,
                                                       recurring, for_new_students, on_campus, religion)
                               VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), to_timestamp(%s), %s, %s, %s, %s, %s,
                                       %s, %s, %s, %s, %s)
                               ''', new_event_rows)
            conn.commit()
            return len(new_event_rows)
        finally:
            cursor.close()
    finally:
        conn.close()


def get_s3_event_ids(bucket):
    folder_path = "backend/chunked/"
    suffix = ".json"
    event_ids = set()

    for obj in bucket.objects.filter(Prefix=folder_path):
        if obj.key == folder_path or not obj.key.endswith(suffix):
            continue
        event_ids.add(obj.key.removeprefix(folder_path).removesuffix(suffix))

    return event_ids


def remove_events_from_s3(bucket, event_ids):
    if not event_ids:
        return

    bucket.delete_objects(Delete={"Objects": [{"Key": f"backend/chunked/{event_id}.json"} for event_id in event_ids]})


def upload_chunk_file_to_s3(bucket, file_name):
    local_file_path = "backend/chunking_tmp_dir/" + file_name + ".json"
    s3_file_path = "backend/chunked/" + file_name + ".json"
    bucket.upload_file(local_file_path, s3_file_path)


def sync_s3_knowledge_base():
    client = boto3.client("bedrock-agent", aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")
    client.start_ingestion_job(knowledgeBaseId=os.getenv("AWS_BEDROCK_KNOWLEDGE_BASE_ID"),
                               dataSourceId=os.getenv("AWS_BEDROCK_DATA_SOURCE_ID"))


def upload_all_events_to_s3(bucket, events):
    print("\nSyncing events to S3...")

    events_dict = {event._id: event for event in events}
    new_event_ids = set(events_dict.keys())

    event_ids_in_db = [i._id for i in get_events_from_db()]
    event_ids_in_s3 = get_s3_event_ids(bucket)

    old_event_ids = [i for i in event_ids_in_s3 if (i not in new_event_ids) and (i not in event_ids_in_db)]
    events_to_add_to_s3 = [i for i in new_event_ids if i not in event_ids_in_s3]

    remove_events_from_s3(bucket, old_event_ids)

    for event_id in events_to_add_to_s3:
        event = events_dict[event_id]
        create_event_chunk_file(event)
        upload_chunk_file_to_s3(bucket, event_id)

    clear_directory("backend/chunking_tmp_dir/")
    clear_directory("backend/event_image_tmp_dir/")

    print(f"\nUploaded {len(events_to_add_to_s3)} new events to S3, removed {len(old_event_ids)} old events, "
          f"and {'synced' if events_to_add_to_s3 or old_event_ids else 'skipped syncing'} Bedrock knowledge base.")

    if events_to_add_to_s3 or old_event_ids:
        time.sleep(3)
        sync_s3_knowledge_base()


def upload_to_db_and_s3(bucket):
    events = load_events_from_file()

    print(f"\nChecking {len(events)} events for database upload...")
    uploaded_event_count = save_events_to_db(events)
    print(f"Uploaded {uploaded_event_count} new events to database.")

    upload_all_events_to_s3(bucket, events)


def main(bucket_name, days_out):
    update_events_file(bucket_name, days_out)

    bucket = boto3.resource("s3").Bucket(bucket_name)
    upload_to_db_and_s3(bucket)


if __name__ == "__main__":
    start = time.time()
    load_dotenv()

    main(os.getenv("S3_BUCKET_NAME"), days_out=60)

    end = time.time()
    print(f"\nFinished in {round((end - start), 1)} seconds.")
