import json, uuid

import boto3

from mod_medicaid.ViaConnection import ViaConnection
from mod_medicaid.AWS_Data_Operations import dd_new_trip


def api_handler(event, context):
    # Obtain header information
    ep = event['requestContext']['resourcePath']
    try:
        payload = json.loads(event['body'])
    except:
        print('No Payload')
        payload = ''
    status_code = 200
    print(payload)
    print(ep)
    output = event

    # Legacy Lyft TAPI code
    if ep == '/v1/tapi/trips/{trip_id}/cancel':
        output = 'Not Available'
        status_code = 404
    elif ep == '/v1/tapi/trips/{trip_id}':
        output = 'Not Available'
        status_code = 404
    elif ep == '/v1/tapi/trips':
        output = 'Not Available'
        status_code = 404
    elif ep == '/kiosk_status' or ep == '/connector_status':
        try:
            vc = ViaConnection()
            output = vc.via_kiosk_trip_status(payload)
        except ValueError as e:
            output = str(e)
            status_code = 200
        except SystemError as e:
            output = str(e)
            status_code = 400
    # NOTE: Kiosk request was broken into two separate calls to keep the
    #           API calls under 30 seconds per API Gateway limits
    elif ep == '/kiosk_request' or ep == '/connector':
        try:
            vc = ViaConnection()
            output = vc.via_request_book_trip(payload)
            dd_new_trip(via_response=output)             
        except ValueError as e:
            output = str(e)
            status_code = 200
        except SystemError as e:
            output = str(e), 500
            # TODO: need to let front end accept this error code
            # status_code = 500
    elif ep == '/kiosk_request_detail':
        try:
            vc = ViaConnection()
            output = vc.via_trip_details(payload['trip_id'])
        except SystemError as e:
            print(e)
            output = str(e)

    # Legacy Code
    elif ep == '/via_webhook':
        try:
            # Legacy code here for future use for MOD-Medicaid
            output = ''
        except Exception as e:
            print(e)
            output = ''
    elif ep == '/v1/tapi/providers':
        output = 'Not Available'
        status_code = 404
    return {
        'isBase64Encoded': False,
        'statusCode': status_code,
        'body': json.dumps(output),
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    }

# Legacy code
def lambda_kiosk(event, context):
    return api_handler(event, context)

def lambda_kiosk_status(event, context):
    return api_handler(event, context)