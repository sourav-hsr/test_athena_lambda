import json
import boto3

def hsr_upload_to_db(s3_bucket, s3_path, db_table_name, table_state, data_type, geometry_type="MULTIPOLYGON", geometry_crs="4326"):
    cloudwatch_events = boto3.client('events')
    if data_type == "geometry":
        # Creating eventbridge events
        event_payload = {
            "eventType": "uploadToDB",
            "s3_bucket": f"{s3_bucket}",
            "s3_path": f"{s3_path}", 
            "db_table_name": f"{db_table_name}",
            "table_state": f"{table_state}",
            "data_type": f"{data_type}",
            "geometry_type": f"{geometry_type}",
            "geometry_crs": f"{geometry_crs}",
            "region": "us-east-1"
        }
    else:
        # Creating eventbridge events
        event_payload = {
            "eventType": "uploadToDB",
            "s3_bucket": f"{s3_bucket}",
            "s3_path": f"{s3_path}", 
            "db_table_name": f"{db_table_name}",
            "table_state": f"{table_state}",
            "data_type": f"{data_type}",
            "region": "us-east-1"
        }
    full_event = {
        "Detail": json.dumps(event_payload),
        "DetailType": "uploadToDB",
        "Source": "uploadToDBEvent",
        "EventBusName": "stg-hsr-event-bus"
    }
    event_response = cloudwatch_events.put_events(Entries = [full_event])

def hsr_download_data(dataName, dataOrganization, dataRecency, dataUpdateFrequency, downloadUrl, downloadType, destBucket, destPath, zipFileName="None", updateGlue="no"):
    cloudwatch_events = boto3.client('events')
    if zipFileName != "None":
        event_payload = {
            "eventType": "downloadData",
            "dataName": dataName,
            "dataOrganization": dataOrganization,
            "dataRecency": dataRecency,
            "dataUpdateFrequency": dataUpdateFrequency,
            "downloadUrl": downloadUrl,
            "zipFileName": zipFileName,
            "downloadType": downloadType,
            "destination": {
                "destBucket": destBucket,
                "destPath": destPath
            },
            "updateGlue": updateGlue
        }
    else:
        event_payload= {
            "eventType": "downloadData",
            "dataName": dataName,
            "dataOrganization": dataOrganization,
            "dataRecency": dataRecency,
            "dataUpdateFrequency": dataUpdateFrequency,
            "downloadUrl": downloadUrl,
            "downloadType": downloadType,
            "destination": {
                "destBucket": destBucket,
                "destPath": destPath
            },
            "updateGlue": updateGlue
        }
    full_event = {
        "Detail": json.dumps(event_payload),
        "DetailType": "downloadData",
        "Source": "downloadDataEvent",
        "EventBusName": "stg-hsr-event-bus"
    }
    event_resposne = cloudwatch_events.put_events(Entries = [full_event])

def hsr_athena_query(database, bucket, path, fileName, query):
    cloudwatch_events = boto3.client('events')
    event_payload = {
        "eventType":"athenaScript",
        "database": database,
        "bucket": bucket,
        "path": path,
        "fileName": fileName,
        "query": query
    }
    full_event = {
        'Detail': json.dumps(event_payload),
        'DetailType': 'athenaScript', 
        'Source': 'athenaScriptEvent',
        'EventBusName': 'stg-hsr-event-bus'
    }
    event_resposne = cloudwatch_events.put_events(Entries = [full_event])