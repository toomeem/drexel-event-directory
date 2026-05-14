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

## Event Sources

| Source | Data |
|---|---|
| [DragonLink](https://drexel.campuslabs.com/engage/) | Student organization events |
| [Drexel Events](https://drexel.edu/events/) | University-wide events and academic programming |
| [Drexel Athletics](https://drexeldragons.com/) | Home and away athletic competitions |
