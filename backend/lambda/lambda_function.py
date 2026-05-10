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
    start_time = db_entry[6]
    end_time = db_entry[7]
    if datetime.now().strftime("%m/%d") == end_time.strftime("%m/%d"):
        time_str_prefix = "Today"
    elif (start_time - datetime.now()) > timedelta(days=7):
        time_str_prefix = datetime.strftime(start_time, "%b %d")
    else:
        time_str_prefix = datetime.strftime(start_time, "%a")
    time_str = (time_str_prefix +
                " - " +
                datetime.strftime(start_time, "%-I:%M") +
                "-" +
                datetime.strftime(end_time, "%-I:%M %p")
                )
    perks = db_entry[11]
    if perks:
        perks = [i for i in perks.split("|") if i]
    return {
        "id": db_entry[0],
        "source": db_entry[1],
        "name": db_entry[2],
        "org_name": db_entry[3],
        "location": db_entry[4],
        "image_url": db_entry[5],
        "time": time_str.replace(":00", ""),
        "event_link": db_entry[8],
        "event_status": db_entry[9],
        "theme": db_entry[10],
        "perks": perks,
    }


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}


def lambda_handler(event, context):
    EVENT_ROWS_PER_PAGE = 6
    EVENTS_PER_ROW = 4
    page_event_count = EVENT_ROWS_PER_PAGE * EVENTS_PER_ROW
    now = datetime.now()
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    params = event.get("queryStringParameters") or {}
    try:
        offset = max((int(params.get("page", 1)) - 1) * page_event_count, 0)
    except (ValueError, TypeError):
        offset = 0
    date_filter = params.get("dateRange")
    date_end = 9999999999
    if date_filter == "today":
        date_end = (datetime(year=now.year, month=now.month, day=now.day) + timedelta(days=1)).timestamp()
    elif date_filter == "week":
        date_end = (now + timedelta(days=7)).timestamp()
    elif date_filter == "month":
        date_end = (now + timedelta(days=30)).timestamp()
    event_status = params.get("event_status")
    if event_status not in ("in-person", "virtual", "hybrid"):
        event_status = None
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
                '''
                SELECT id,
                       source,
                       name,
                       org_name,
                       location,
                       image_url,
                       start_time,
                       end_time,
                       event_link,
                       event_status,
                       theme,
                       perks,
                       COUNT(*) OVER () AS total_count
                FROM main.events
                WHERE (end_time + INTERVAL '1 hour') > now()
                  AND start_time <= to_timestamp(%s)
                  AND (%s IS NULL OR event_status = %s)
                ORDER BY start_time
                LIMIT %s OFFSET %s
                ''',
                (date_end, event_status, event_status, page_event_count, offset))
            events = cursor.fetchall()

        total = events[0][12] if events else 0
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "statusCode": 200,
                "total_events": total,
                "body": [db_entry_to_json(e) for e in events],
            }),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"statusCode": 500, "body": str(e)}),
        }
