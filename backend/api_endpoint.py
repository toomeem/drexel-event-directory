import json
import os
from datetime import timedelta, datetime
from pprint import pprint

import psycopg2
from dotenv import load_dotenv


def db_entry_to_json(db_entry):
    if (db_entry[5] - datetime.now()) > timedelta(days=7):
        time_str_prefix = datetime.strftime(db_entry[5], "%b %d, ")
    else:
        time_str_prefix = datetime.strftime(db_entry[5], "%a ")
    time_str = time_str_prefix + datetime.strftime(db_entry[5], "%#I:%M") + "-" + datetime.strftime(db_entry[6],
                                                                                                    "%#I:%M %p")
    return {
        "id": db_entry[0],
        "source": db_entry[1],
        "name": db_entry[2],
        "org_name": db_entry[3],
        "location": db_entry[4],
        "time": time_str.replace(":00", ""),
        "image_url": db_entry[7],
    }


def retrieve_events(count=12):
    load_dotenv()
    with psycopg2.connect(
            host=os.getenv("RDS_ENDPOINT"),
            database="postgres",
            user="postgres",
            password=os.getenv("RDS_PASSWORD"),
            port="5432"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT id,
                       source,
                       name,
                       org_name,
                       location,
                       start_time,
                       end_time,
                       image_url
                FROM main.events
                WHERE end_time > now()
                ORDER BY start_time ASC
                LIMIT {count}
                ''')
            events = cursor.fetchall()
    return json.dumps({
        "statusCode": 200,
        "body": [db_entry_to_json(event) for event in events]
    })


if __name__ == "__main__":
    pprint(retrieve_events())
