import os
import sys
import traceback
import boto3
import json
import pandas as pd
from datetime import datetime
import time
import re
import urllib.parse
import io
import re

# Required for lambda relative pathing
sys.path.append(os.path.join(os.path.dirname(__file__)))
from lib.appFunctions import *

session = boto3.Session()
s3 = boto3.resource("s3")
cloudwatch_events = boto3.client('events')
#out_bucket = "stg-hsr-authoritative-data"

def athena_query(client, params):
    response = client.start_query_execution(
        QueryString=params["query"],
        QueryExecutionContext={
            'Database': params['database']
        },
        ResultConfiguration={
            'OutputLocation': 's3://' + params['bucket'] + '/' + params['path']
        }
    )
    return response

def renameResult(session, params, queryfilename):
    query_loc = f'{params["bucket"]}/{params["path"]}/{queryfilename}'
    print(f"Query Loc: {query_loc}")
    time.sleep(10)
    if params["conversion"] == "parquet":
        # Copy query file to file with proper name
        df = pd.read_csv(f's3://{query_loc}.csv')
        df.to_parquet(f"s3://{params['bucket']}/{params['path']}/{params['fileName']}.parquet.gzip", compression='gzip')
        print(f"Output Location: s3://{params['bucket']}/{params['path']}/{params['fileName']}.parquet.gzip")
    else:
        response1 = s3.Object(params['bucket'], f"{params['path']}/{params['fileName']}.csv").copy_from(f"{params['bucket']}/{params['path']}/{queryfilename}.csv")
        print(f"Output Location: s3://{params['bucket']}/{params['path']}/{params['fileName']}.csv")
    # Delete the original athena outputs
    response = s3.Object(params['bucket'], f"{params['path']}/{queryfilename}.csv").delete()
    response = s3.Object(params['bucket'], f"{params['path']}/{queryfilename}.csv.metadata").delete()
    print(f"{params['fileName']} csv generated")

def athena_to_s3(session, params, max_execution = 5):
    try:
        client = session.client('athena', region_name="us-east-1")
        execution = athena_query(client, params)
        execution_id = execution['QueryExecutionId']
        state = 'RUNNING'
        while (max_execution > 0 and state in ['RUNNING', 'QUEUED']):
            #max_execution = max_execution - 1
            response = client.get_query_execution(QueryExecutionId = execution_id)
            if 'QueryExecution' in response and  'Status' in response['QueryExecution'] and 'State' in response['QueryExecution']['Status']:
                state = response['QueryExecution']['Status']['State']
                if state == 'FAILED':
                    print("Query Failed")
                    print(response['QueryExecution']['Status']['StateChangeReason'])
                    failSlack(params, response['QueryExecution']['Status']['StateChangeReason'])
                    #print(response)
                    return False
                elif state == 'SUCCEEDED':
                    s3_path = response['QueryExecution']['ResultConfiguration']['OutputLocation']
                    time.sleep(5)
                    filename = execution_id
                    renameResult(session, params, filename)
                    succSlack(params)
                    return filename
            time.sleep(1)
        return False
    except Exception:
        print(traceback.print_exc())
        failSlack(params, traceback.format_exc(limit=2))

print('Loading function')
def tri_processing_part1(year, month, day):
    covid_d_range = pd.date_range(start='2020-03-28', end = f'{year}-{month}-{day}')
    covid_d_range = "', '".join(list(covid_d_range.strftime('%Y-%m-%d'))[-30:])
    cum_cases = 'confirmed'
    cum_deaths = 'deaths'
    cum_active = '(confirmed - deaths)'
    rec_date = "CONCAT(partition_0, '-', partition_1, '-', partition_2)"
    global_key = "CONCAT(country_region, '-', province_state, '-', admin2)"
    universal_key = f"CONCAT(country_region, '-', province_state, '-', admin2, '-', {rec_date})"
    # Calculating Daily Cases, Deaths, and Active
    daily_cases = f'({cum_cases} - lag({cum_cases}, 1, {cum_cases}) over (partition by {global_key} order by {rec_date}))'
    daily_deaths = f'({cum_deaths} - lag({cum_deaths}, 1, {cum_deaths}) over (partition by {global_key} order by {rec_date}))'
    daily_active = f'CASE WHEN ({cum_active} - lag({cum_active}, 1, {cum_active}) over (partition by {global_key} order by {rec_date})) < 0 THEN 0 WHEN ({cum_active} - lag({cum_active}, 1, {cum_active}) over (partition by {global_key} order by {rec_date})) >= 0 THEN ({cum_active} - lag({cum_active}, 1, {cum_active}) over (partition by {global_key} order by {rec_date})) END'
    # Calculating 30, 14, and 7 day sums of active cases, cases, and deaths
    cases_30d = f'(SUM(daily_cases) over (partition by global_key order by rec_date rows between 30 preceding and current row))'
    cases_14d = f'(SUM(daily_cases) over (partition by global_key order by rec_date rows between 14 preceding and current row))'
    cases_7d = f'(SUM(daily_cases) over (partition by global_key order by rec_date rows between 7 preceding and current row))'
    deaths_30d = f'(SUM(daily_deaths) over (partition by global_key order by rec_date rows between 30 preceding and current row))'
    deaths_14d = f'(SUM(daily_deaths) over (partition by global_key order by rec_date rows between 14 preceding and current row))'
    deaths_7d = f'(SUM(daily_deaths) over (partition by global_key order by rec_date rows between 7 preceding and current row))'
    active_30d = f'(SUM(daily_active) over (partition by global_key order by rec_date rows between 30 preceding and current row))'
    active_14d = f'(SUM(daily_active) over (partition by global_key order by rec_date rows between 14 preceding and current row))'
    active_7d = f'(SUM(daily_active) over (partition by global_key order by rec_date rows between 7 preceding and current row))'
    # Calculating Crude Fatality Ratio
    cfr_cum = f'CASE WHEN cum_cases = 0 THEN 0 WHEN cum_cases > 0 THEN ROUND(cum_deaths / cum_cases * 100, 4) END'
    cfr_30d = f'CASE WHEN {cases_30d} = 0 THEN 0 WHEN {cases_30d} > 0 THEN ROUND({deaths_30d} / {cases_30d} * 100, 4) END'
    cfr_14d = f'CASE WHEN {cases_14d} = 0 THEN 0 WHEN {cases_14d} > 0 THEN ROUND({deaths_14d} / {cases_14d} * 100, 4) END'
    cfr_7d = f'CASE WHEN {cases_7d} = 0 THEN 0 WHEN {cases_7d} > 0 THEN ROUND({deaths_7d} / {cases_7d} * 100, 4) END'
    # Building SQL Statement 
    sql_statement = f"""with new as (SELECT fips, admin2, province_state, country_region, last_update, lat, long_, combined_key, {cum_cases} as cum_cases, {cum_deaths} as cum_deaths, {cum_active} as cum_active, {rec_date} as rec_date, {global_key} as global_key, {universal_key} as universal_key, {daily_cases} as daily_cases, {daily_deaths} as daily_deaths, {daily_active} as daily_active 
FROM "stg-authdatadb"."covid_jhu" WHERE {rec_date} in ('{covid_d_range}')) 
SELECT t2.* from new t1 
JOIN( SELECT *, {cases_30d} as cases_30d, {cases_14d} as cases_14d, {cases_7d} as cases_7d, {deaths_30d} as deaths_30d, {deaths_14d} as deaths_14d, {deaths_7d} as deaths_7d, {active_30d} as active_30d, {active_14d} as active_14d, {active_7d} as active_7d, {cfr_cum} as cfr_cum, {cfr_30d} as cfr_30d, {cfr_14d} as cfr_14d, {cfr_7d} as cfr_7d from new) t2 
ON t1.universal_key = t2.universal_key WHERE t2.rec_date = '{year}-{month}-{day}'"""
    print(sql_statement)
    return(sql_statement)

def tri_processing_part2(year, month, day):
    covid_d_range = pd.date_range(start='2020-03-28', end = f'{year}-{month}-{day}')
    covid_d_range = "', '".join(list(covid_d_range.strftime('%Y-%m-%d'))[-7:])
    # Calculating Daily Percent Change
    pctc_daily_cases = f'CASE WHEN (lag(daily_cases, 1, daily_cases) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(daily_cases, 1, daily_cases) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((daily_cases - (lag(daily_cases, 1, daily_cases) over (partition by global_key order by rec_date))) / (lag(daily_cases, 1, daily_cases) over (partition by global_key order by rec_date)), 4) END'
    pctc_daily_deaths = f'CASE WHEN (lag(daily_deaths, 1, daily_deaths) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(daily_deaths, 1, daily_deaths) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((daily_deaths - (lag(daily_deaths, 1, daily_deaths) over (partition by global_key order by rec_date))) / (lag(daily_deaths, 1, daily_deaths) over (partition by global_key order by rec_date)), 4) END'
    pctc_daily_active = f'CASE WHEN (lag(daily_active, 1, daily_active) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(daily_active, 1, daily_active) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((daily_active - (lag(daily_active, 1, daily_active) over (partition by global_key order by rec_date))) / (lag(daily_active, 1, daily_active) over (partition by global_key order by rec_date)), 4) END'
    pctc_active_30d = f'CASE WHEN (lag(active_30d, 1, active_30d) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(active_30d, 1, active_30d) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((active_30d - (lag(active_30d, 1, active_30d) over (partition by global_key order by rec_date))) / (lag(active_30d, 1, active_30d) over (partition by global_key order by rec_date)), 4) END'
    pctc_active_14d = f'CASE WHEN (lag(active_14d, 1, active_14d) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(active_14d, 1, active_14d) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((active_14d - (lag(active_14d, 1, active_14d) over (partition by global_key order by rec_date))) / (lag(active_14d, 1, active_14d) over (partition by global_key order by rec_date)), 4) END'
    pctc_active_7d = f'CASE WHEN (lag(active_7d, 1, active_7d) over (partition by global_key order by rec_date)) = 0 THEN 0 WHEN (lag(active_7d, 1, active_7d) over (partition by global_key order by rec_date)) <> 0 THEN ROUND((active_7d - (lag(active_7d, 1, active_7d) over (partition by global_key order by rec_date))) / (lag(active_7d, 1, active_7d) over (partition by global_key order by rec_date)), 4) END'
    # Calculating Weekly Average Percent Change
    ccr_daily_cases = f'ROUND(AVG(pctc_daily_cases) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    ccr_daily_deaths = f'ROUND(AVG(pctc_daily_deaths) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    ccr_daily_active = f'ROUND(AVG(pctc_daily_active) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    ccr_active_30d = f'ROUND(AVG(pctc_active_30d) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    ccr_active_14d = f'ROUND(AVG(pctc_active_14d) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    ccr_active_7d = f'ROUND(AVG(pctc_active_7d) over (partition by global_key order by rec_date rows between 7 preceding and current row), 4)'
    statement = f"""with new as (SELECT *, {pctc_daily_cases} as pctc_daily_cases, {pctc_daily_deaths} as pctc_daily_deaths, {pctc_daily_active} as pctc_daily_active, {pctc_active_30d} as pctc_active_30d, {pctc_active_14d} as pctc_active_14d, {pctc_active_7d} as pctc_active_7d FROM "stg-internaldatadb"."covidjhustage1" WHERE rec_date in ('{covid_d_range}')) SELECT t2.* from new t1 JOIN( SELECT *, {ccr_daily_cases} as ccr_daily_cases, {ccr_daily_deaths} as ccr_daily_deaths, {ccr_daily_active} as ccr_daily_active, {ccr_active_30d} as ccr_active_30d, {ccr_active_14d} as ccr_active_14d, {ccr_active_7d} as ccr_active_7d FROM new) t2 ON t1.universal_key = t2.universal_key WHERE t2.rec_date = '{year}-{month}-{day}'"""
    print(statement)
    return(statement)

def tri_processing_part3(year, month, day):
    glue = boto3.client('glue')
    print(glue.get_table(DatabaseName='stg-internaldatadb',
    Name='covidjhustage2')['Table']['StorageDescriptor']['Columns'])
    col_lista = []
    col_listb = []
    for col in glue.get_table(DatabaseName='stg-internaldatadb', Name='covidjhustage2')['Table']['StorageDescriptor']['Columns']:
        col_lista.append(col['Name'])
    col_lista = [x for x in col_lista if x not in ['fips', 'admin2', 'province_state', 'country_region', 'last_update', 'lat', 'long_', 'combined_key', 'global_key', 'universal_key']]
    col_lista = ", ".join(col_lista)
    for col in glue.get_table(DatabaseName='stg-internaldatadb', Name='mripartitioned')['Table']['StorageDescriptor']['Columns']:
        col_listb.append(col['Name'])
    col_listb = [x for x in col_listb[:14] if x not in ['year']]
    col_listb = ", ".join(col_listb)
    # Calculating Rate for specific metrics
    metrics = ['daily_cases', 'daily_deaths', 'daily_active', 'cases_30d', 'deaths_30d', 'active_30d', 'cases_14d', 'deaths_14d', 'active_14d', 'cases_7d', 'deaths_7d', 'active_7d']
    mlist = [f"ROUND(({x} / b.e_pop) * 100000, 4) as rte_{x}" for x in metrics]
    mlist = ", ".join(mlist)
    statement = f""" SELECT b.*, {col_lista}, {mlist} FROM "stg-internaldatadb"."covidjhustage2" a JOIN(SELECT {col_listb} FROM "stg-internaldatadb"."mripartitioned") b ON lpad(cast(cast(a.fips as bigint) as varchar), 5, '0') = lpad(cast(b.geom_id as varchar), 5, '0') WHERE a.rec_date = '{year}-{month}-{day}'"""
    print(col_listb)
    print(statement)
    return(statement)

def handler(event, context):
    try:
        print("Received event: " + json.dumps(event))
        if 'Detail' in event:
            event_payload = event['Detail']
        elif 'detail' in event:
            event_payload = event['detail']
        else:
            event_payload = event
        query_list = []

        if event_payload['stage'] == '01':
            sql_statement = tri_processing_part1(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event = {
                "eventType":"athenaScript",
                "database": "stg-authdatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/covidJHU/covidJHU/covidJHUStage1",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-stg1",
                "conversion": event_payload['conversion'],
                "stage": "01",
                "query": sql_statement
            }
            # query_list.append(athena_event)
            s3_filename = athena_to_s3(session, athena_event) 
        elif event_payload['stage'] == '02':
            sql_statement = tri_processing_part2(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event = {
                "eventType":"athenaScript",
                "database": "stg-internaldatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/covidJHU/covidJHU/covidJHUStage2",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-stg2",
                "conversion": event_payload['conversion'],
                "stage": "02",
                "query": sql_statement
            }
            # query_list.append(athena_event)
            s3_filename = athena_to_s3(session, athena_event)
        elif event_payload['stage'] == '03':
            sql_statement = tri_processing_part3(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event = {
                "eventType":"athenaScript",
                "database": "stg-internaldatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/covidJHU/covidJHU/usCovidJHU",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-us",
                "conversion": event_payload['conversion'],
                "stage": "03",
                "query": sql_statement
            }
            # query_list.append(athena_event)
            s3_filename = athena_to_s3(session, athena_event)
        elif event_payload['stage'] == 'all':
            sql_statement1 = tri_processing_part1(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event1 = {
                "eventType":"athenaScript",
                "database": "stg-authdatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/processedAuthData/covidJHU/covidJHUStage1",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-stg1",
                "conversion": event_payload['conversion'],
                "stage": "01",
                "query": sql_statement1
            }
            # query_list.append(athena_event1)
            s3_filename = athena_to_s3(session, athena_event1)
            sql_statement2 = tri_processing_part2(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event2 = {
                "eventType":"athenaScript",
                "database": "stg-internaldatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/processedAuthData/covidJHU/covidJHUStage2",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-stg2",
                "conversion": event_payload['conversion'],
                "stage": "02",
                "query": sql_statement2
            }
            s3_filename = athena_to_s3(session, athena_event2)
            sql_statement3 = tri_processing_part3(event_payload['year'], event_payload['month'], event_payload['day'])
            athena_event3 = {
                "eventType":"athenaScript",
                "database": "stg-internaldatadb",
                "bucket": "stg-hsr-internal-data-products",
                "path": "processedAuthData/processedAuthData/covidJHU/usCovidJHU",
                "fileName": f"{event_payload['year']}-{event_payload['month']}-{event_payload['day']}-us",
                "conversion": event_payload['conversion'],
                "stage": "03",
                "query": sql_statement3
            }
            s3_filename = athena_to_s3(session, athena_event3)
        
        final_events = []
        for x in query_list:
            out = {
                'Detail': json.dumps(x),
                'DetailType': 'athenaScript', 
                'Source': 'athenaScriptEvent',
                'EventBusName': 'stg-hsr-event-bus'
            }
            final_events.append(out)

        # Creating Put Events for the event bus
        print(final_events)
        for f in final_events:
            response = cloudwatch_events.put_events(
                Entries = [f]
            )
            print(response['Entries'])

        return {
            'statusCode': 200,
            'body': json.dumps('Success')
        }
    except Exception:
        print('Failed')
        traceback.print_exc(Exception)