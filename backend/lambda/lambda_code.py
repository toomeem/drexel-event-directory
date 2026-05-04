import json
import os
from datetime import timedelta, datetime

import boto3
import psycopg2

proxy_host_name = os.environ["RDS_ENDPOINT"]
db_user_name = "postgres"
db_name = "drexel-event"
user = "postgres"
aws_region = "us-east-1"
password = os.environ["RDS_PASSWORD"]
port = 5432


def get_auth_token():
    client = boto3.client('rds')
    token = client.generate_db_auth_token(
        DBHostname=proxy_host_name,
        Port=port,
        DBUsername=db_user_name,
        Region=aws_region,
    )
    return token


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
    token = get_auth_token()
    try:
        connection = psycopg2.connect(
            host=proxy_host_name,
            user=db_user_name,
            password=token,
            dbname=db_name,
            port=port,
            ssl={'ca': 'Amazon RDS'}  # Ensure you have the CA bundle for SSL connection
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
                ORDER BY start_time ASC
                LIMIT {event['count']}
                ''')
            events = cursor.fetchall()
        return json.dumps({
            "statusCode": 200,
            "body": [db_entry_to_json(event) for event in events]
        })
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
