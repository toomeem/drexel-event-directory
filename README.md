# Drexel Event Hub

A web app that aggregates upcoming events from across Drexel University into a single, filterable directory — with an AI-powered chatbot assistant.

Live at: [toomeem.github.io/drexel-event-directory](https://toomeem.github.io/drexel-event-directory)

## Features

- Browse upcoming events from DragonLink, Drexel.edu, and Drexel Athletics
- Filter by theme (academic, arts, social, athletics, etc.), event format (in-person, virtual, hybrid), and perks (free food, credit, etc.)
- AI chatbot (AWS Bedrock Agent + Knowledge Base) for natural language event queries
- Light/dark mode
  

## Project Structure

```
drexel-event-directory/
├── frontend/          # React + TypeScript + Vite app
└── backend/
    ├── collect_events.py      # Scrapes and normalizes events from all sources
    ├── event_class.py         # Event data model
    ├── chatbot_lambda.py      # AWS Lambda handler for the chatbot API
    ├── lambda/                # Lambda deployment package source
    │   ├── lambda_function.py
    │   └── requirements.txt
    └── Makefile               # Builds and zips the main  website Lambda deployment package
```

## Local Development

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # fill in VITE_LAMBDA_ENDPOINT and VITE_CHATBOT_LAMBDA_ENDPOINT
npm run dev
```

### Backend — Event Collection

Requires Python 3.14+ and the packages in `backend/lambda/requirements.txt`, plus `openai`, `psycopg2`, and `python-dotenv`.

```bash
cd backend
cp .env.example .env   # fill in all required values
python collect_events.py
```

Running `collect_events.py` will:
1. Fetch events from DragonLink, Drexel.edu, and Drexel Athletics
2. Normalize and deduplicate them
3. Save to `events.json`
4. Write to the PostgreSQL (RDS) database
5. Upload individual event JSON files to S3 (for the Bedrock Knowledge Base)

## Environment Variables

### Backend (`.env` / Lambda environment)

| Variable | Description |
|---|---|
| `RDS_ENDPOINT` | PostgreSQL host |
| `RDS_USERNAME` | PostgreSQL username |
| `RDS_PASSWORD` | PostgreSQL password |
| `OPENAI_API_KEY` | Used to classify event locations (in-person / virtual / hybrid) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for S3 uploads |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for S3 uploads |
| `S3_BUCKET_NAME` | S3 bucket that backs the Bedrock Knowledge Base |
| `AWS_BEDROCK_AGENT_ID` | Bedrock Agent ID (chatbot Lambda only) |
| `AWS_BEDROCK_AGENT_ALIAS_ID` | Bedrock Agent Alias ID (chatbot Lambda only) |
| `AWS_BEDROCK_KNOWLEDGE_BASE_ID` | Bedrock Knowledge Base ID (chatbot Lambda only) |

### Frontend (`.env`)

| Variable | Description |
|---|---|
| `VITE_LAMBDA_ENDPOINT` | API Gateway URL for the events Lambda |
| `VITE_CHATBOT_LAMBDA_ENDPOINT` | API Gateway URL for the chatbot Lambda |

## Deployment

### Frontend

Pushing to `main` triggers the GitHub Actions workflow (`.github/workflows/deploy.yml`), which builds the frontend and deploys it to GitHub Pages automatically.

### Backend Lambda

```bash
cd backend
make          # cleans, installs dependencies, and zips the package
```

Upload `backend/lambda_package.zip` to your AWS Lambda function.

## Event Sources

| Source | Data |
|---|---|
| [DragonLink](https://drexel.campuslabs.com/engage/) | Student organization events |
| [Drexel Events](https://drexel.edu/events/) | University-wide events and academic programming |
| [Drexel Athletics](https://drexeldragons.com/) | Home and away athletic competitions |
