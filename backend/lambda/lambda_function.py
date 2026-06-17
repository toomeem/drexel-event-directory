import json
import os
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

import psycopg2

PHILLY_TZ = ZoneInfo("America/New_York")

proxy_host_name = os.environ["RDS_ENDPOINT"]
db_user_name = "postgres"
db_name = "postgres"
password = os.environ["RDS_PASSWORD"]
port = 5432


def _fmt_hm(dt, with_ampm=False):
    h = dt.strftime("%I").lstrip("0") or "12"
    return f"{h}:{dt.strftime('%M %p')}" if with_ampm else f"{h}:{dt.strftime('%M')}"


def make_time_str(start_time, end_time):
    now = datetime.now(PHILLY_TZ)
    if end_time - start_time > timedelta(hours=24):
        if (start_time - now) > timedelta(days=7):
            return datetime.strftime(start_time, "%a - ") + datetime.strftime(end_time, "%a")
        return f"{start_time.strftime('%b')} {start_time.day} - {end_time.day}"

    if now.strftime("%m/%d") == start_time.strftime("%m/%d"):
        time_str_prefix = "Today"
    elif (now + timedelta(days=1)).strftime("%m/%d") == start_time.strftime("%m/%d"):
        time_str_prefix = "Tomorrow"
    elif (start_time - now) > timedelta(days=7):
        time_str_prefix = f"{start_time.strftime('%b')} {start_time.day}"
    else:
        time_str_prefix = datetime.strftime(start_time, "%A")
    return f"{time_str_prefix} - {_fmt_hm(start_time)}-{_fmt_hm(end_time, with_ampm=True)}"


def db_entry_to_json(db_entry):
    start_time = db_entry[6].astimezone(PHILLY_TZ)
    end_time = db_entry[7].astimezone(PHILLY_TZ)

    time_str = make_time_str(start_time, end_time)
    if db_entry[11]:
        perks = [i for i in db_entry[11].split("|") if i]
    else:
        perks = None
    return {"id": db_entry[0], "source": db_entry[1], "name": db_entry[2], "org_name": db_entry[3],
            "location": db_entry[4], "image_url": db_entry[5], "time": time_str.replace(":00", ""),
            "start_time": round(start_time.timestamp()) if start_time else None,
            "end_time": round(end_time.timestamp()) if end_time else None, "event_link": db_entry[8],
            "event_status": db_entry[9], "theme": db_entry[10], "perks": perks, "food_related": db_entry[12],
            "popular": db_entry[13], "weekly": db_entry[14], "for_new_students": db_entry[15],
            "on_campus": db_entry[16], "religion": db_entry[17], }


MAX_SEARCH_LEN = 100
VALID_PERKS = {"free_food", "free_stuff", "credit"}

CORS_HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin", "Content-Type": "application/json", }


def lambda_handler(event, context):
    EVENT_ROWS_PER_PAGE = 6
    EVENTS_PER_ROW = 4
    MAX_PAGE = 1000

    page_event_count = EVENT_ROWS_PER_PAGE * EVENTS_PER_ROW
    now = datetime.now(PHILLY_TZ)
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    params = event.get("queryStringParameters") or {}
    try:
        page = max(1, min(int(params.get("page", 1)), MAX_PAGE))
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * page_event_count
    date_filter = params.get("dateRange")
    date_end = 9999999999
    if date_filter == "today":
        date_end = (datetime(year=now.year, month=now.month, day=now.day, tzinfo=PHILLY_TZ) + timedelta(
            days=1)).timestamp()
    elif date_filter == "week":
        date_end = (now + timedelta(days=7)).timestamp()
    elif date_filter == "month":
        date_end = (now + timedelta(days=30)).timestamp()
    event_status = params.get("event_status")
    if event_status not in ("in-person", "online", "hybrid"):
        event_status = None
    valid_themes = {"academic", "arts", "athletics", "career", "community", "cultural", "fundraising", "social",
                    "spirituality"}
    themes = None
    theme_param = params.get("theme")
    if theme_param:
        candidates = [t.strip().lower() for t in theme_param.split(",")]
        themes = [t for t in candidates if t in valid_themes] or None
    perks_filter = None
    perks_param = params.get("perks")
    if perks_param:
        candidates = [p.strip().lower() for p in perks_param.split(",") if p.strip()]
        perks_filter = [p for p in candidates if p in VALID_PERKS] or None
    search_pattern = None
    search_param = params.get("search")
    if search_param:
        s = search_param.strip()[:MAX_SEARCH_LEN]
        if s:
            s = s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            search_pattern = f"%{s}%"

    def parse_bool_filter(name):
        val = params.get(name)
        return val is not None and val.strip().lower() in ("1", "true", "yes")

    food_related = parse_bool_filter("food_related")
    weekly = parse_bool_filter("weekly")
    for_new_students = parse_bool_filter("for_new_students")
    popular = parse_bool_filter("popular")
    on_campus = parse_bool_filter("on_campus")
    religion = parse_bool_filter("religion")
    connection = None
    try:
        connection = psycopg2.connect(host=proxy_host_name, user=db_user_name, password=password, dbname=db_name,
                                      port=port, sslmode='require')
        with connection.cursor() as cursor:
            cursor.execute('''
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
                                  food_related,
                                  popular,
                                  weekly,
                                  for_new_students,
                                  on_campus,
                                  religion,
                                  COUNT(*) OVER () AS total_count
                           FROM main.events
                           WHERE end_time > now()
                             AND start_time <= to_timestamp(%s)
                             AND (%s IS NULL OR event_status = %s)
                             AND (%s::text[] IS NULL OR LOWER(theme) = ANY (%s::text[]))
                             AND (%s::text[] IS NULL OR string_to_array(LOWER(perks), '|') && %s::text[])
                             AND (%s::text IS NULL OR name ILIKE %s OR org_name ILIKE %s)
                             AND (NOT %s OR food_related)
                             AND (NOT %s OR weekly)
                             AND (NOT %s OR for_new_students)
                             AND (NOT %s OR popular)
                             AND (NOT %s OR on_campus)
                             AND (NOT %s OR religion IS NOT NULL)
                           ORDER BY start_time, id
                           LIMIT %s OFFSET %s
                           ''', (date_end, event_status, event_status, themes, themes, perks_filter, perks_filter,
                                 search_pattern, search_pattern, search_pattern, food_related, weekly, for_new_students,
                                 popular, on_campus, religion, page_event_count, offset))
            events = cursor.fetchall()

        total = events[0][18] if events else 0
        return {"statusCode": 200, "headers": CORS_HEADERS,
                "body": json.dumps({"total_events": total, "body": [db_entry_to_json(e) for e in events]})}

    except Exception as e:
        print(f"lambda_handler error: {e!r}")
        return {"statusCode": 500, "headers": CORS_HEADERS, "body": json.dumps({"error": "Internal Server Error"})}
    finally:
        if connection is not None:
            connection.close()
