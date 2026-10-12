import os
import time

import boto3
import pg8000.dbapi
from dotenv import load_dotenv

from backend.python_files.event_class import Event
from backend.python_files.event_sources.bbj_events import BBJEventSource
from backend.python_files.event_sources.dragonlink_event_functions import DragonlinkEventSource
from backend.python_files.event_sources.drexel_athletics_event_functions import DrexelAthleticsEventSource
from backend.python_files.event_sources.drexel_event_functions import DrexelEventSource
from backend.python_files.event_sources.static_recurring_events import StaticRecurringEventSource
from backend.python_files.event_sources.ucity_district_events import UCityDistrictEventSource
from backend.python_files.event_sources.ucity_square_event_functions import UCitySquareEventSource
from backend.python_files.helper_functions import is_invalid_event, simplify_org_name, get_event_status, \
    match_default_image, simplify_location, is_food_related, is_popular, is_recurring, is_for_new_students, \
    is_on_campus, clear_directory, create_event_chunk_file, load_events_from_file, save_events_to_file, \
    manual_event_fixes, simplify_event_name, enrich_perks, event_theme_additional_checks, get_religion
from backend.python_files.image_parsing_functions import get_image_s3_url

EVENT_SOURCE_TYPES = (
    StaticRecurringEventSource,
    UCityDistrictEventSource,
    BBJEventSource,
    DragonlinkEventSource,
    DrexelAthleticsEventSource,
    UCitySquareEventSource,
    DrexelEventSource,
)
SOURCE_PRIORITIES = {source_type.name: source_type.priority for source_type in EVENT_SOURCE_TYPES}


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
    return [Event.from_db_row(row) for row in simple_events_in_db()]


def create_event_object(event_source, event_data, bucket_name):
    event_fields = {"_id": None, "source": event_source.name, "name": None, "org_name": None, "location": None,
                    "image_url": None, "start_time": None, "end_time": None, "event_link": None,
                    "event_status": None, "theme": None, "perks": [], "food_related": False, "popular": False,
                    "recurring": False, "for_new_students": False, "on_campus": True, "religion": None,
                    "description": ""}

    event_fields = event_source.parse(event_data, event_fields)
    if is_invalid_event(event_fields):
        return None

    event_fields["perks"] = enrich_perks(
        event_fields["name"], event_fields["description"], event_fields["perks"])
    event_fields["org_name"] = simplify_org_name(
        event_fields["org_name"], event_fields["name"], event_fields["description"])
    event_fields["name"] = simplify_event_name(event_fields["name"])
    event_fields["event_status"] = get_event_status(event_source.name, event_fields["location"])

    if event_fields["image_url"] is None:
        event_fields["image_url"] = get_image_s3_url(
            match_default_image(event_fields["name"], event_fields["org_name"], event_fields["location"]), bucket_name)
    else:
        event_fields["image_url"] = get_image_s3_url(event_fields["image_url"], bucket_name)
        if event_fields["image_url"] is None:
            event_fields["image_url"] = get_image_s3_url(
                match_default_image(
                    event_fields["name"], event_fields["org_name"], event_fields["location"]), bucket_name)

    if event_fields["event_status"] == "online":
        event_fields["location"] = "Online"
    else:
        event_fields["location"] = simplify_location(event_fields["location"])
        if event_fields["location"] is None:
            return None

    event_fields["food_related"] = is_food_related(
        event_fields["name"], event_fields["perks"], event_fields["location"], event_fields["description"])
    event_fields["recurring"] = is_recurring(event_fields["name"], event_fields["description"])
    event_fields["for_new_students"] = is_for_new_students(event_fields["name"], event_fields["description"])
    event_fields["on_campus"] = is_on_campus(
        event_fields["name"], event_fields["org_name"], event_fields["location"])
    event_fields["religion"] = get_religion(
        event_fields["name"], event_fields["org_name"], event_fields["location"])

    if event_fields["religion"]:
        event_fields["theme"] = "spirituality"
        event_fields["popular"] = False
    else:
        event_fields["theme"] = event_theme_additional_checks(
            event_fields["name"], event_fields["description"], event_fields["org_name"],
            event_fields["location"], event_fields["theme"])
        event_fields["popular"] = is_popular(event_fields["name"])

    del event_fields["description"]
    return Event(**event_fields)


def dedup_events(events_in_db, events):
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
            result.append(max(cluster, key=lambda event: SOURCE_PRIORITIES[event.source]))

    result.sort(key=lambda e: e.start_time.timestamp())
    return result


def collect_all_events(bucket_name, events_in_db, days_out):
    existing_event_ids = [i._id for i in events_in_db]
    event_sources = [
        source_type(bucket_name, existing_event_ids, days_out)
        for source_type in EVENT_SOURCE_TYPES
    ]
    events = []

    for event_source in event_sources:
        event_count = len(events)
        for event_data in event_source.collect():
            if event_data is None:
                continue
            event = create_event_object(event_source, event_data, bucket_name)
            if event is not None:
                events.append(event)

        print(f"Collected {len(events) - event_count} events from {event_source.name}.")

    events = [manual_event_fixes(event) for event in events]
    events = [event for event in events if not event.is_out_of_range(days_out)]
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
    local_file_path = "backend/temp_folders/chunking_tmp_dir/" + file_name + ".json"
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

    clear_directory("backend/temp_folders/chunking_tmp_dir/")
    clear_directory("backend/temp_folders/event_image_tmp_dir/")

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
