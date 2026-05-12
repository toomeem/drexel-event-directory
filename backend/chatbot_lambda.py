import json
import os
import uuid

import boto3

AGENT_ID = os.environ['AWS_BEDROCK_AGENT_ID']
AGENT_ALIAS_ID = os.environ['AWS_BEDROCK_AGENT_ALIAS_ID']
MAX_INPUT_LEN = 400


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


def lambda_handler(event, context):
    try:
        input_text = sanitize_input(event.get('input', ''))
    except ValueError as e:
        return {'statusCode': 400, 'body': json.dumps({'error': str(e)})}

    bedrock = boto3.client(service_name='bedrock-agent-runtime', region_name='us-east-1')
    response = bedrock.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=event.get('id') or str(uuid.uuid4().hex),
        inputText=input_text,
    )

    completion = ""
    for chunk_event in response['completion']:
        chunk = chunk_event.get('chunk')
        if chunk and 'bytes' in chunk:
            completion += chunk['bytes'].decode('utf-8')

    return {'statusCode': 200, 'body': json.dumps({'completion': completion})}
