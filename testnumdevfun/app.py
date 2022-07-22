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
        print("Received eventx: " + json.dumps(event))
        # This if block handles the formatting that happens when it is invoked by an event from event bridge
        if 'Detail' in event:
            event_payload = event['Detail']
        elif 'detail' in event:
            event_payload = event['detail']
        else:
            event_payload = event



        DATABASE = 'stg-authdatadb'
        TABLE='sgcbgcensus'
        TABLE2='home_panel_summary'
        output='s3://stg-hsr-athena/bri-refactor/Sourav_test_athena/docker_github_actions_results/'


        STATE=event_payload['state'].lower()
        DATE=event_payload['date']

        print(STATE)
        print(DATE)

        #query = """ SELECT * FROM "stg-authdatadb"."sgcbgcensus" """
        query=("SELECT b.number_devices_residing,"
        "b.census_block_group,"
        "c.b01001e1, "
        "b.date_range_start "
        f"""FROM "{DATABASE}"."{TABLE}" c """
        f"""LEFT OUTER JOIN "{DATABASE}"."{TABLE2}" b ON lpad(replace(c.census_block_group, '.0'), 12, '0') = lpad(replace(replace(b.census_block_group, 'CA:',''), '.0', ''), 12, '0') """
        f"""WHERE b.region = '{STATE}' """
        f"""and lpad(b.date_range_start, 10, '0') = '{DATE}' """)
        print(query)
        client = boto3.client('athena')
        # Execution
        response = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': DATABASE
            },
            ResultConfiguration={
                'OutputLocation': output,
            }
        )

        
        result=client.get_query_execution(QueryExecutionId=response["QueryExecutionId"])

        print(result)


        return result["OutputLocation"]

        
    except Exception:
        print('Failed')
        traceback.print_exc(Exception)