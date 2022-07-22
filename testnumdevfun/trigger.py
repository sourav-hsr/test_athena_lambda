def trigger():

	# 
	cloudwatch_events = boto3.client('events')

	# create payload
	payload = {
		  "key1": "value1",
		  "state": "MD",
		  "date": "2021-06-28"
	}

	# send to eventbus
	full_event = {
	    "Detail": json.dumps(payload),
	    "DetailType": "testnumdevfun",
	    "Source": "testnumdevfunEvent",
	    "EventBusName": "stg-hsr-event-bus"
	}


	event_response = cloudwatch_events.put_events(Entries = [full_event])	

	return 0