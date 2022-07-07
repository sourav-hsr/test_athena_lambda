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
    DATABASE = 'stg-authdatadb'
    TABLE='sgcbgcensus'
    TABLE2='home_panel_summary'
    output='s3://stg-hsr-athena/bri-refactor/Sourav_test_athena/docker_github_actions_results/'


    STATE=event['state'].lower()
    DATE=event['date']

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
    return response