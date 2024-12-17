import json
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

import os
# from .lyft_via_xform import lyft_to_via, via_to_lyft
from .via_request import via_request_trip, via_cancel_trip

def dd_new_trip(lyft_trip_data, atms_ride_id, via_response):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('MOD_Medicaid')

    #input data for table insertion
    tapi_trip_id = str(lyft_trip_data['tapi_trip_id'])
    via_trip_id = via_response['trip_id']
    lyft_request_payload = json.dumps(lyft_trip_data)
    via_response_payload = json.dumps(via_response)

    # Insert items into table.
    table.put_item(Item={
        "request_time": str(datetime.now()),
        "atms_ride_id": atms_ride_id,
        "tapi_trip_id": tapi_trip_id, 
        "via_trip_id":via_trip_id, 
        "lyft_request_payload": lyft_request_payload, 
        "via_response_payload": via_response_payload
    })
        
def dd_get_via_trip_id(tapi_trip_id):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('MOD_Medicaid')

    projection_expression = "via_trip_id"

    # Define the filter expression
    filter_expression = Key('tapi_trip_id').eq(tapi_trip_id)
    
    rows = table.scan(
        ProjectionExpression=projection_expression,
        FilterExpression=filter_expression
    )
    
    # Access the scanned items
    items = rows['Items'][0]
    via_trip_id = items['via_trip_id']

    return via_trip_id 


def dd_history_entry(old_entry):
    # Prepare the DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    history_table = dynamodb.Table("MOD_Medicaid_History")
    old_entry['update_time'] = str(int(round(datetime.now().timestamp(), 0)))

    history_table.put_item(Item=old_entry)


# Check rows:
def dd_retrieve_data(tapi_trip_id):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('MOD_Medicaid')
    filter_expression = Key('tapi_trip_id').eq(tapi_trip_id)
    rows = table.scan(
        FilterExpression=filter_expression
    )

    # Access the scanned items
    items = rows['Items'][0]

    return(items)
    

def dd_retrieve_by_via_trip_id(via_trip_id):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table('MOD_Medicaid')
    filter_expression = Key('via_trip_id').eq(via_trip_id)
    rows = table.scan(
        FilterExpression=filter_expression
    )

    # Access the scanned items
    items = rows['Items'][0]

    return(items)

if __name__ == "__main__":
    os.environ["TABLE_NAME"] = "MOD_Medicaid"
    test_event = {  "tapi_trip_id": "1234tapi_new", "lyft_request_payload": "lyft_request_payload_type1",\
                   "via_trip_id": "1234via_new",  "via_response_payload": "via_response_payload_type1"}
    result = api_handler(test_event, None)
    print(result)
