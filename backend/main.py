import json
import os
import time
from datetime import datetime

import boto3
import psycopg2
from backend.python_files.event_data_parsing_functions import make_time_str, create_event_object, \
    collect_dragonlink_events, collect_drexel_events, create_drexel_athletics_events, openai_client
from dotenv import load_dotenv
from event_class import Event


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
    update_events_file(openai_client)  # fill_db()  # upload_all_events_to_s3()


if __name__ == "__main__":
    start = time.time()
    load_dotenv()

    main()

    end = time.time()
    print(f"\nFinished in {round((end - start) / 60, 1)} mins.")
