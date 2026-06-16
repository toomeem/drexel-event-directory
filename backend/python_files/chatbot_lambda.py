import json
import os
import re
import uuid

import boto3

AGENT_ID = os.environ['AWS_BEDROCK_AGENT_ID']
AGENT_ALIAS_ID = os.environ['AWS_BEDROCK_AGENT_ALIAS_ID']
KNOWLEDGE_BASE_ID = os.environ['AWS_BEDROCK_KNOWLEDGE_BASE_ID']
MAX_INPUT_LEN = 400
MAX_CHUNKS = 15

# sanitize session ids
SESSION_ID_RE = re.compile(r"^[0-9a-f]{32}$")

CORS_HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin", "Content-Type": "application/json", }


def _response(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def sanitize_input(value):
    if not isinstance(value, str):
        raise ValueError("input must be a string")
    cleaned = "".join(c for c in value if c == "\n" or c == "\t" or (c.isprintable() and ord(c) >= 0x20))
    cleaned = cleaned.strip()
    if not cleaned:
        raise ValueError("input must not be empty")
    if len(cleaned) > MAX_INPUT_LEN:
        raise ValueError(f"input must be {MAX_INPUT_LEN} characters or fewer")
    return cleaned


def resolve_session_id(raw):
    if isinstance(raw, str) and SESSION_ID_RE.match(raw):
        return raw
    return uuid.uuid4().hex


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    if 'body' in event:
        try:
            payload = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        except (ValueError, TypeError):
            return _response(400, {"error": "invalid JSON body"})
    else:
        payload = event
    if not isinstance(payload, dict):
        return _response(400, {"error": "invalid payload"})

    try:
        input_text = sanitize_input(payload.get('input', ''))
    except ValueError as e:
        return _response(400, {"error": str(e)})

    session_id = resolve_session_id(payload.get('id'))

    bedrock = boto3.client(service_name='bedrock-agent-runtime', region_name='us-east-1')
    response = bedrock.invoke_agent(agentId=AGENT_ID, agentAliasId=AGENT_ALIAS_ID, sessionId=session_id,
                                    inputText=input_text, sessionState={'knowledgeBaseConfigurations': [
            {'knowledgeBaseId': KNOWLEDGE_BASE_ID,
             'retrievalConfiguration': {'vectorSearchConfiguration': {'numberOfResults': MAX_CHUNKS}}}]})

    completion = ""
    for chunk_event in response['completion']:
        chunk = chunk_event.get('chunk')
        if chunk and 'bytes' in chunk:
            completion += chunk['bytes'].decode('utf-8')

    return _response(200, {"completion": completion, "session_id": session_id})
