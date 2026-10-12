# Drexel Event Hub

A web app that aggregates upcoming events from across Drexel University into a single, filterable directory — with an
AI-powered chatbot assistant.

Live at: [drexeleventhub.com](https://www.drexeleventhub.com/)

## Features

- Browse upcoming events from five scraped calendars plus hand-curated recurring listings
- Rich filtering: theme (academic, arts, social, athletics, etc.), event format (in-person, online, hybrid), perks (free
  food, free stuff, etc.), date range (today / week / month), religion, and flags like on-campus, popular, recurring,
  and new-student events
- Keyword search across event and organization names
- Light/dark theme toggle
- Events API served from AWS Lambda, backed by a PostgreSQL (RDS) database
- AI chatbot (AWS Bedrock Agent + S3 Knowledge Base) for natural language event queries

## Architecture

```
                ┌─────────────┐
   Sources ───▶ │ main.py     │ ──────────┬─────────────────┬──────────────────┐
 (scrapers)     └─────────────┘           ▼                 ▼                  ▼
                                  PostgreSQL (RDS)   S3 Image Storage  Bedrock Knowledge Base
                                          ▲                 ▲              for RAG
                                          │                 │                  ▲
                                 ┌────────┴───────┐         │        ┌─────────┴───────┐
                                 │ Events Lambda  │         │        │ Chatbot Lambda  │
                                 └────────────────┘         │        └─────────────────┘
                                          ▲                 │                  ▲
                                          │        ┌────────┴───────┐          │
                                          └────────┤Frontend (React)├──────────┘
                                                   └────────────────┘
```

- `backend/python_files/main.py` collects all sources, de-duplicates events, inserts them into PostgreSQL, streams event
  images and knowledge-base event chunks to S3, and starts a Bedrock knowledge-base ingestion job.
- The events Lambda queries PostgreSQL with the active filters and returns paginated results to the frontend.
- The chatbot Lambda proxies user questions from the frontend to a Bedrock Agent backed by the S3 knowledge base.

## Project Structure

```
drexel-event-directory/
├── .github/workflows/
│   └── deploy.yml                         # GitHub Pages and AWS frontend deployment
├── frontend/                              # React + TypeScript + Vite app
│   ├── public/
│   └── src/
│       ├── api/                           # Events and chatbot API clients
│       ├── components/                    # Cards, filters, header, and chatbot widget
│       └── pages/                         # Events and About pages
└── backend/
    ├── data_files/                        # Rules, defaults, and hand-curated event definitions
    │   ├── static_recurring_events.json
    │   └── static_single_events.json      # Present but not currently loaded by the pipeline
    ├── python_files/
    │   ├── main.py                        # Collects, de-duplicates, and uploads events
    │   ├── event_class.py                 # Event data model
    │   ├── event_sources/                 # Per-source collectors and parsers
    │   │   ├── event_source.py
    │   │   ├── dragonlink_event_functions.py
    │   │   ├── drexel_event_functions.py
    │   │   ├── drexel_athletics_event_functions.py
    │   │   ├── ucity_square_event_functions.py
    │   │   ├── ucity_district_events.py
    │   │   └── static_recurring_events.py
    │   ├── helper_functions.py            # Normalization and tagging rules
    │   ├── image_parsing_functions.py     # Image processing and S3 upload
    │   ├── lambda_function.py             # Events API Lambda handler
    │   ├── chatbot_lambda.py              # Chatbot Lambda handler
    │   └── testing.py
    ├── requirements.txt                   # Events Lambda package dependencies
    └── Makefile                           # Builds the events Lambda deployment package
```

## Event Sources

| Source                                                            | Collection method                                              |
|-------------------------------------------------------------------|----------------------------------------------------------------|
| [Drexel Events](https://drexel.edu/events/)                       | University-wide events and academic programming                |
| [DragonLink](https://drexel.campuslabs.com/engage/)               | Student organization events                                    |
| [Drexel Athletics](https://drexeldragons.com/)                    | Home and away athletic competitions                            |
| [uCity Square](https://ucitysquare.com/events/month/)             | Neighborhood events on The Lawn near campus                    |
| [University City District](https://www.universitycity.org/events) | District-wide public programming and community events          |
| Local Restaurants and Venues                                      | Hand-curated weekly listings in `static_recurring_events.json` |

## Backend

The Lambda build targets Python 3.14. The collection pipeline additionally imports `boto3`, `beautifulsoup4`, and
`Pillow`; these are not included in `backend/requirements.txt`, which is currently scoped to the events Lambda package.

### Collecting events

`backend/python_files/main.py` orchestrates the pipeline: it collects each source, removes duplicates (preferring more
authoritative sources), inserts new rows into PostgreSQL, streams images and per-event JSON chunks to S3, and syncs
the chatbot's Bedrock knowledge base.

```bash
# run from the repository root
python3 -m pip install -r backend/requirements.txt boto3 beautifulsoup4 Pillow
cp backend/python_files/.env.example backend/python_files/.env

# Export the file because the pipeline is launched from the repository root.
set -a
source backend/python_files/.env
set +a
python3 -m backend.python_files.main
```

The pipeline expects an existing PostgreSQL `main.events` table. Required environment variables:

- `RDS_ENDPOINT`, `RDS_USERNAME`, `RDS_PASSWORD` — PostgreSQL connection
- `S3_BUCKET_NAME` — S3 bucket for event images and `backend/chunked/` knowledge-base documents
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` — AWS credentials
- `AWS_BEDROCK_KNOWLEDGE_BASE_ID`, `AWS_BEDROCK_DATA_SOURCE_ID` — Bedrock knowledge base sync

### Tests

The backend test suite runs entirely offline. It covers the event models, rule helpers, static recurring-event
definitions and scheduling, source parsers, pipeline de-duplication, time formatting, and image resizing.

```bash
# From the repository root:
python3 -m unittest discover -s backend/tests -v

# Or:
make -C backend test
```

### Events API (Lambda)

`python_files/lambda_function.py` serves paginated, filtered event results from PostgreSQL. Build the deployment
package with:

```bash
cd backend
make
```

This installs the dependencies in `requirements.txt` for `manylinux2014_x86_64` and produces
`lambda_package.zip`. Required Lambda environment variables: `RDS_ENDPOINT`, `RDS_USERNAME`, and `RDS_PASSWORD`.

### Chatbot API (Lambda)

`python_files/chatbot_lambda.py` proxies sanitized user input to a Bedrock Agent. Required environment variables:
`AWS_BEDROCK_AGENT_ID`, `AWS_BEDROCK_AGENT_ALIAS_ID`, `AWS_BEDROCK_KNOWLEDGE_BASE_ID`.

## Frontend

A React + TypeScript app built with Vite.

```bash
cd frontend
npm ci
npm run dev      # start the dev server
npm run build    # type-check and build for production
```

The production API endpoints are currently defined in `frontend/src/api/events.ts` and
`frontend/src/api/chatbot.ts`. Pushes to `main` and `dev` deploy GitHub Pages builds; pushes to `main` also deploy the
frontend to S3 and invalidate its CloudFront distribution.
