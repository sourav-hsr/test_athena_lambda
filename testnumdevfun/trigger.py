import boto3
import json


def trigger():

	# 
	cloudwatch_events = boto3.client('events')

	print(cloudwatch_events)

	# create payload
	payload = {
		  "key1": "value1",
		  "state": "MD",
		  "date": "2021-06-28",
		  "eventType":"testnumdevfun"
	}


	print(payload)

	# send to eventbus
	full_event = {
	    "detail": json.dumps(payload),
	    "DetailType": "testnumdevfun",
	    "Source": "testnumdevfunEvent",
	    "EventBusName": "stg-hsr-event-bus"
	}


	event_response = cloudwatch_events.put_events(Entries = [full_event])	

	print(event_response)

	return 0


trigger()