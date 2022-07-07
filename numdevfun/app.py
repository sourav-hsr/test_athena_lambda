import os
import sys
import traceback
import boto3
import json
import time
import re
import urllib.parse
import io
import re

# Required for importing py files from the lib directory of this function if you want that functionality
sys.path.append(os.path.join(os.path.dirname(__file__)))
from lib.appFunctions import *

# The following is the bare minimum you need for the lambda function to run off of an event
def handler(event, context):
    try:
        print("Received event: " + json.dumps(event))
        # This if block handles the formatting that happens when it is invoked by an event from event bridge
        if 'Detail' in event:
            event_payload = event['Detail']
        elif 'detail' in event:
            event_payload = event['detail']
        else:
            event_payload = event
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
    except Exception:
        print('Failed')
        traceback.print_exc(Exception)