"""
mod_medicaid

mod_medicaid serves as the primary logical point to compile the various 
transform and communication code betwen Lyft and Via.  


"""

import json, uuid, os
from pprint import pprint

import sqlalchemy as sa
from sqlalchemy import select

from .lyft_via_xform import lyft_to_via, via_to_lyft
from .via_request import via_request_trip, via_cancel_trip
from datastore import sqlite_db, trip_requests
from .AWS_Data_Operations import dd_new_trip, dd_get_via_trip_id, dd_retrieve_data, dd_history_entry 

environ = os.environ.get('Execution')

def lyft_trip_request(lyft_trip_data):
    """Process Lyft's trip request in Via"""

    # Headers
    # Authorization, x-lyft-program-id
    #
    # Validate incoming data
    # Required fields
    # tapi_trip_id, ride_date, leg_type, pickup_time, origin, destination, rider, trip_source, supplier, invoice_by, reject_by
    #
    # Optional fields
    # appointment_time, demand_additional_info

    # Lyft -> Via Transformation Layer
    # Via API /trips/request
    # Via Requires: arrive_at OR depart_at as epoch
    # Note that Lyft sends data as a YYYY-MM-DDTHH:MM:SS-TZ (ISO 8601)
    # 
    # Required Location: origin and destination, with lat/lng and optional (but recommended) address
    # Required passenger_count
    # Required rider_identifier which takes an object of {rider_id} or {first_name, last_name, phone_number, email}
    #
    # Optional Fields that could use useful:
    # return_trip_depart_at / return_trip_arrive_at
    # trip_properties, additional_passengers
    #
    # Notes from lyft's demand_additional_info can be put into via's origin/destionation object 

    atms_ride_id = str(uuid.uuid4())
    
    # Lyft -> Via Transformation Layer    
    via_request_data = lyft_to_via(lyft_trip_data)

    # Send Data to Via
    try:
        print(via_request_data)
        via_response = via_request_trip(via_request_data)
    except SystemError as e:
        return str(e), 400
    
    # Via -> Lyft Transformation Layer
    lyft_response = via_to_lyft(via_response, lyft_trip_data, atms_ride_id)
    print(lyft_response)

    if environ == 'On_Prem':
        with sqlite_db.connect() as con:
            con.execute(trip_requests.insert(), dict(
                tapi_trip_id=lyft_trip_data['tapi_trip_id'],
                atms_ride_id=atms_ride_id,
                via_trip_id=via_response['trip_id'],
                lyft_request_payload=json.dumps(lyft_trip_data),
                via_response_payload=json.dumps(via_response)
            ))
            con.commit()
    elif environ == 'On_AWS':
        dd_new_trip(lyft_trip_data, atms_ride_id, via_response)


    return lyft_response, 201
    # Need to also build exceptions to 400 Bad Request and 404 Not Found

def lyft_cancel_request(tapi_trip_id):
    """Process Lyft's cancel request in Via"""

    if environ == 'On_Prem':
        with sqlite_db.connect() as con:
            rows = con.execute(
                select(trip_requests.c.via_trip_id)
                .where(trip_requests.c.tapi_trip_id==str(tapi_trip_id)
                )
            )
            for i, row in enumerate(rows):
                if i == 0:
                    via_trip_id = row[0]
                    break
    elif environ == 'On_AWS':
        via_trip_id = dd_get_via_trip_id(tapi_trip_id)

    print(via_trip_id)
    via_response = via_cancel_trip(via_trip_id)
    print(via_response)
    return via_response 

def lyft_update_request(new_lyft_trip_data, tapi_trip_id):
    """Process Lyft's update request in Via"""

    if environ == 'On_Prem':
        with sqlite_db.connect() as con:
            rows = con.execute(
                select((trip_requests.c.via_trip_id, trip_requests.c.lyft_request_payload))
                .where(trip_requests.c.tapi_trip_id==str(tapi_trip_id)
                )
            )
            for i, row in enumerate(rows):
                if i == 0:
                    orig_trip_id = row[0]
                    orig_lyft_req = row[1]
                    break
    elif environ == 'On_AWS':
        # Get original data
        full_data = dd_retrieve_data(tapi_trip_id)
        orig_lyft_req = json.loads(full_data['lyft_request_payload'])
        orig_trip_id = full_data['via_trip_id']


    # Merge the new data with the old data
    new_lyft_request = orig_lyft_req | new_lyft_trip_data

    # Store a history
    dd_history_entry(full_data)
    try:
        # Cancel current ride
        via_cancel_trip(orig_trip_id)
        print(new_lyft_request)
        # and rebook    
        output = lyft_trip_request(new_lyft_request)
    except:
        return ('ATMS Error: Unable to Modify Trip', 500)

    return output 


def kiosk_via_trip_request(via_trip_data):
    try:
        atms_ride_id = str(uuid.uuid4())
        tapi_trip_id = str(uuid.uuid4())
        
        # Send Data to Via
        try:
            via_response_data = via_request_trip(via_trip_data)
        except SystemError as e:
            return str(e), 500

        if environ == 'On_Prem':
            with sqlite_db.connect() as con:
                con.execute(trip_requests.insert(), dict(
                    tapi_trip_id=tapi_trip_id,
                    atms_ride_id=atms_ride_id,
                    via_trip_id=via_response_data['trip_id'],
                    via_response_payload=json.dumps(via_response_data)
                ))
                con.commit()
        elif environ == 'On_AWS':
            dd_new_trip({'tapi_trip_id': tapi_trip_id}, atms_ride_id, via_response_data)

    except SystemError as e:
        print(e)
        return str(e), 500
    return via_response_data, 200