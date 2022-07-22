import boto3
import json
import base64
import os
import sys
import requests
import urllib3

# Importing Secrets
def get_secret(secret_name):
    region_name = "us-east-1"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return json.loads(base64.b64decode(get_secret_value_response['SecretBinary']))

slack_secret = get_secret(f'{os.environ["SECRETS_ARN"]}//hsr//slack-FpgxPx')
url = slack_secret['stg-slack-secret']

def succSlack(event_payload):
    block_payload = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Athena: COVID JHU Data Cleaning Stage {event_payload['stage']}",
                "emoji": True
            }
        }, 
        {
            "type":"section",
            "text":{
                "type":"mrkdwn",
                "text":"*Status:*\n Success"
            }
        },
        {
            "type":"section", 
            "text":{
                "type": "mrkdwn",
                "text": f"*Output Location:*\n {event_payload['path']}/{event_payload['fileName']}"
            }
        }
    ]
    msg = {
        "channel": "#CHANNEL_NAME",
        "username": "Lambda Notifications",
        "text": "TRI Lambda Success Notification",
        "blocks": block_payload,
        "icon_emoji": ""
    }

    payload2 = json.dumps(msg).encode('utf-8')
    print(payload2)
    response = requests.request('POST', url, data=payload2)
    print(response)

def failSlack(event_payload, tracebk):
    block_payload = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Athena: COVID JHU Data Cleaning Stage {event_payload['stage']}",
                "emoji": True
            }
        }, 
        {
            "type":"section",
            "text":{
                "type":"mrkdwn",
                "text":"*Status:*\n Failed"
            }
        },
        {
            "type":"section", 
            "text":{
                "type": "mrkdwn",
                "text": f"*Expected Output Table:*\n {event_payload['path']}/{event_payload['fileName']}"
            }
        },
        {
            "type":"section", 
            "text":{
                "type":"mrkdwn",
                "text":f"*Traceback:*\n {tracebk}"
            }
        }
    ]
    msg = {
        "channel": "#CHANNEL_NAME",
        "username": "Lambda Notifications",
        "text": "Publishing Failed Notification",
        "blocks": block_payload,
        "icon_emoji": ""
    }

    payload2 = json.dumps(msg).encode('utf-8')
    print(payload2)
    response = requests.request('POST', url, data=payload2)
    print(response)