# Drexel Event Hub

A web app that aggregates upcoming events from across Drexel University into a single, filterable directory — with an
AI-powered chatbot assistant.

Live at: [toomeem.github.io/drexel-event-directory](https://toomeem.github.io/drexel-event-directory)

## Features

- Browse upcoming events from DragonLink, Drexel.edu, Drexel Athletics, and UCity Square
- Rich filtering: theme (academic, arts, social, athletics, etc.), event format (in-person, online, hybrid), perks (free
  food, free stuff, credit), date range (today / week / month), religion, and flags like on-campus, popular, recurring,
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

- `main.py` scrapes all sources, de-duplicates events, inserts into PostgreSQL, uploads event
  images to S3, and syncs event "chunks" to a separate S3 bucket for the Bedrock knowledge base.
- The events Lambda queries PostgreSQL with the active filters and returns paginated results to the frontend.
- The chatbot Lambda proxies user questions from the frontend to a Bedrock Agent backed by the S3 knowledge base.

## Project Structure

```
drexel-event-directory/
├── frontend/                  # React + TypeScript + Vite app
│   └── src/
│       ├── api/               # events + chatbot API clients
│       ├── components/        # cards, filters, header, chatbot widget
│       └── pages/             # Events and About pages
└── backend/
    ├── python_files/
    │   ├── main.py                            # Collects, de-dupes, and uploads events (DB + S3)
    │   ├── event_class.py                     # Event data model
    │   ├── event_data_parsing_functions.py    # Source scrapers and normalization
    │   ├── chatbot_lambda.py                  # AWS Lambda handler for the chatbot API
    │   └── testing.py
    ├── lambda/
    │   ├── lambda_function.py                 # AWS Lambda handler for the events API
    │   └── requirements.txt                   # Events Lambda dependencies
    ├── json_examples/                         # Sample raw responses from each source
    ├── events.json                            # Latest collected event snapshot
    └── Makefile                               # Builds and zips the events Lambda deployment package
```

## Event Sources

| Source                                              | Data                                            |
|-----------------------------------------------------|-------------------------------------------------|
| [DragonLink](https://drexel.campuslabs.com/engage/) | Student organization events                     |
| [Drexel Events](https://drexel.edu/events/)         | University-wide events and academic programming |
| [Drexel Athletics](https://drexeldragons.com/)      | Home and away athletic competitions             |
| [UCity Square](https://ucitysquare.com/)            | Neighborhood and community events near campus   |

## Backend

The data pipeline and APIs run on Python 3.14.

### Collecting events

`main.py` orchestrates the pipeline: it scrapes each source, removes duplicates (preferring more authoritative sources),
saves a snapshot to `events.json`, inserts new rows into PostgreSQL, and syncs per-event JSON chunks to S3 for the
chatbot's Bedrock knowledge base.

```bash
# run from the repository root
python -m backend.python_files.main
```

Required environment variables (via a `.env` file):

- `RDS_ENDPOINT`, `RDS_USERNAME`, `RDS_PASSWORD` — PostgreSQL connection
- `S3_BUCKET_NAME` — bucket for event images and knowledge-base chunks
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` — AWS credentials
- `AWS_BEDROCK_KNOWLEDGE_BASE_ID`, `AWS_BEDROCK_DATA_SOURCE_ID` — Bedrock knowledge base sync

### Events API (Lambda)

`lambda/lambda_function.py` serves paginated, filtered event results from PostgreSQL. Build the deployment package with:

```bash
cd backend
make
```

This installs the dependencies in `lambda/requirements.txt` for `manylinux2014_x86_64` and produces
`lambda_package.zip`. Required Lambda environment variables: `RDS_ENDPOINT` and `RDS_PASSWORD`.

### Chatbot API (Lambda)

`python_files/chatbot_lambda.py` proxies sanitized user input to a Bedrock Agent. Required environment variables:
`AWS_BEDROCK_AGENT_ID`, `AWS_BEDROCK_AGENT_ALIAS_ID`, `AWS_BEDROCK_KNOWLEDGE_BASE_ID`.

## Frontend

A React + TypeScript app built with Vite.

```bash
cd frontend
npm install
npm run dev      # start the dev server
npm run build    # type-check and build for production
```
