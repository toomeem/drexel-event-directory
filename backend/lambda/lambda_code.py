import json
import os
from datetime import timedelta, datetime

import psycopg2

proxy_host_name = os.environ["RDS_ENDPOINT"]
db_user_name = "postgres"
db_name = "postgres"
user = "postgres"
aws_region = "us-east-1"
password = os.environ["RDS_PASSWORD"]
port = 5432


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


def lambda_handler(event, context):
    offset = (int(event.get("page", 1)) - 1) * 12
    try:
        connection = psycopg2.connect(
            host=proxy_host_name,
            user=db_user_name,
            password=password,
            dbname=db_name,
            port=port,
            sslmode='require'
        )
        with connection.cursor() as cursor:
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
                ORDER BY start_time 
                LIMIT 12 OFFSET {offset}
                ''')
            events = cursor.fetchall()
        return json.dumps({
            "statusCode": 200,
            "body": [db_entry_to_json(event) for event in events]
        })
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
