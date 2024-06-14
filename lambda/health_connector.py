import json, uuid

import boto3

from mod_medicaid import mod_medicaid, via_request, webhooks


def api_handler(event, context):
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
    if ep == '/v1/tapi/trips/{trip_id}/cancel':
        output = mod_medicaid.lyft_cancel_request(event['pathParameters']['trip_id'])
        status_code = 204
    elif ep == '/v1/tapi/trips/{trip_id}':
        output = mod_medicaid.lyft_update_request(payload, event['pathParameters']['trip_id'])
        status_code = 204
    elif ep == '/v1/tapi/trips':
        output, status_code = mod_medicaid.lyft_trip_request(payload)
        # status_code = 201
    elif ep == '/kiosk_status' or ep == '/connector_status':
        try:
            output = via_request.via_check_status(payload)
        except SystemError as e:
            output = str(e)
            status_code = 400
    elif ep == '/kiosk_request' or ep == '/connector':
        try:
            output = mod_medicaid.kiosk_via_trip_request(payload)
            if False: #not isinstance(output, tuple):
                try:
                    request_detail = via_request.via_trip_details({"trip_id": output['trip_id']})
                    output = output | request_detail
                except SystemError as e:
                    output = str(e)
            else:
                return {
                    # FIx later
                    'isBase64Encoded': False,
                    'statusCode': output[1],
                    'body': json.dumps(output[0]),
                    'headers': {
                        'content-type': 'application/json',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    }
                }
                # status_code = output[1]
                # output = output[0]                
        except SystemError as e:
            output = str(e)
    elif ep == '/kiosk_request_detail':
        try:
            output =  via_request.via_trip_details(payload)
        except SystemError as e:
            print(e)
            output = str(e)
    elif ep == '/via_webhook':
        output = webhooks.via_interpreter(payload, event)
    elif ep == '/v1/tapi/providers':
        output = {
            "transportation_providers": [{
                "data_source_supplier_id": "hirta",
                "data_source_supplier_name": "HIRTA - Heart of Iowa Regional Transportation Authority",
                "data_source_supplier_city": "Urbandale",
                "data_source_supplier_state": "Iowa",
                "data_source_supplier_phone": "+18776860029",
                "data_source_supplier_email": "info@ridehirta.com",
                "data_source_supplier_enabled": True
            }]
        }

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

def lambda_lyft_tapi_trips_v1(event, context):
    try:
        resp = mod_medicaid.lyft_trip_request(json.loads(event['body']))
    except:
        resp = event
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': json.dumps(resp),
        'headers': {
            'content-type': 'application/json'
        }
    }    

def lambda_lyft_tapi_cancel_v1(event, context):
    try:
        resp = mod_medicaid.lyft_trip_request(json.loads(event['body']))
    except:
        resp = event
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': json.dumps(resp),
        'headers': {
            'content-type': 'application/json'
        }
    }

def lambda_kiosk(event, context):
    # # via_request_trip,
    # try:
    #     resp = via_request.via_trip_request(json.loads(event['body']))
    # except:
    #     resp = event
    # return {
    #     'isBase64Encoded': False,
    #     'statusCode': 200,
    #     'body': json.dumps(resp),
    #     'headers': {
    #         'content-type': 'application/json',
    #         'Access-Control-Allow-Headers': 'Content-Type',
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    #     }
    # } 
    return api_handler(event, context)

def lambda_kiosk_status(event, context):
    # resp = mod_medicaid.direct_via_check_status(json.loads(event['body']))
    resp = via_request.via_check_status(json.loads(event['body']))
    # try:
    # except:
    #     resp = event
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': json.dumps(resp),
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        }
    } 

def dashboard_handler(event, context):
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': '{ dashboard: true }',
        'headers': {
            'content-type': 'application/json'
        }
    }