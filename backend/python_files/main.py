import json
import os
import time
from datetime import datetime
from pprint import pprint

import pg8000.dbapi

import boto3
from backend.python_files.event_class import Event
from backend.python_files.event_data_parsing_functions import make_time_str, create_event_object, \
    collect_dragonlink_events, collect_drexel_events, collect_drexel_athletics_events, get_all_ucity_square_urls, \
    create_ucity_square_event_from_url, stable_hash
from dotenv import load_dotenv


def create_event_chunk_file(event):
    path = "backend/chunking_tmp_dir/" + event._id + ".json"
    event_json = event.to_json()
    event_json["formatted_time_str"] = make_time_str(event.start_time, event.end_time)
    del event_json["event_link"]
    del event_json["image_url"]
    del event_json["id"]
    del event_json["start_time"]
    del event_json["end_time"]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(event_json, f)


def clear_directory(path):
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


def clear_s3_folder(bucket):
    folder_path = "backend/chunked/"
    bucket.objects.filter(Prefix=folder_path).delete()


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


def event_ids_db():
    conn = pg8000.dbapi.connect(host=os.getenv("RDS_ENDPOINT"), database="postgres", user=os.getenv("RDS_USERNAME"),
                                password=os.getenv("RDS_PASSWORD"), port=5432, ssl_context=True)
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM main.events")
            return {row[0] for row in cursor.fetchall()}
        finally:
            cursor.close()
    finally:
        conn.close()


def collect_all_events(bucket_name):
    existing_event_ids = event_ids_db()
    events = []

    ucity_square_urls = [i for i in get_all_ucity_square_urls(months_out=3) if stable_hash(i) not in existing_event_ids]
    half_ucity_square_urls = len(ucity_square_urls) // 2
    events.extend(
        [create_ucity_square_event_from_url(url, bucket_name) for url in ucity_square_urls[:half_ucity_square_urls]])
    events = [e for e in events if e is not None]
    event_count = len(events)
    print(f"\nCollected {event_count} UCity Square events.")

    events.extend(
        [create_event_object("dragonlink", event_json, bucket_name, existing_event_ids) for event_json in
         collect_dragonlink_events(count=300)])
    events = [e for e in events if e is not None]
    print(f"Collected {len(events) - event_count} Dragonlink events.")
    event_count = len(events)

    events.extend(
        [create_event_object("drexel_events", event_json, bucket_name, existing_event_ids) for event_json in
         collect_drexel_events(count=200)])
    events = [e for e in events if e is not None]
    print(f"Collected {len(events) - event_count} Drexel events.")
    event_count = len(events)

    events.extend(
        [create_event_object("drexel_athletics", event_json, bucket_name, existing_event_ids) for event_json in
         collect_drexel_athletics_events(days_out=90)])
    events = [e for e in events if e is not None]
    print(f"Collected {len(events) - event_count} Drexel Athletics events.")
    event_count = len(events)

    events.extend(
        [create_ucity_square_event_from_url(url, bucket_name) for url in ucity_square_urls[half_ucity_square_urls:]])
    print(f"Collected {len(events) - event_count} more UCity Square events.")

    source_priority = {"drexel_events": 0, "drexel_athletics": 1, "dragonlink": 2, "ucity_square": 3, "other": 4, }

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


def fill_db(events):
    print(f"\nChecking {len(events)} events for database upload...")
    uploaded_event_count = save_events_to_db(events)
    print(f"Uploaded {uploaded_event_count} new events to database.")


def update_events_file(bucket_name):
    print("\nCollecting events...")
    events = collect_all_events(bucket_name)
    save_events_to_file(events)
    print(f"\nSaved {len(events)} events to file.")


def upload_all_events_to_s3(bucket, events):
    print("\nSyncing events to S3...")

    events_dict = {event._id: event for event in events}
    new_event_ids = set(events_dict.keys())

    event_ids_in_db = event_ids_db()
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
    fill_db(events)
    upload_all_events_to_s3(bucket, events)


def main():
    s3_client = boto3.client(service_name="s3", aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"), region_name="us-east-1")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    bucket = boto3.resource("s3").Bucket(bucket_name)

    update_events_file(bucket_name)
    upload_to_db_and_s3(bucket)


if __name__ == "__main__":
    start = time.time()
    load_dotenv()

    main()

    end = time.time()
    print(f"\nFinished in {round((end - start), 1)} seconds.")
