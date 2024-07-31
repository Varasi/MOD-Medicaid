"""
Flask Server

The purpose of this server is to demonstrate the effectivenes of the 
external resources necessary to power the ITS4US Middleware effectively 
without relying on complex infrastructure.  This server relies solely on

* Flask
* SQlite via SQAlchemy 

to operate and could be transformed to operate independently on a single
node instance instead cloud infrastructure.  **IMPORTANTLY** the operator
of this instance needs to ensure that all cybersecurity measures are taken,
such as:

* proper authentication for Lyft via the TAPI api and OAuth2
* proper storage of private keys to authenticate against various EHR using FHIR

This server's primary functionn is for debugging functions built in Python and
testing third party connectivity without the complexity of AWS 

"""

from pprint import pprint

import flask
from flask import Flask

from mod_medicaid.mod_medicaid import lyft_trip_request, lyft_cancel_request, lyft_update_request, via_request_trip
import os

os.environ["Execution"] = "On_Prem" 

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!!!!!!!!!!!!!!!!!!!!!</p>"

# Some Authentication Wrapper Here Would exist if we did a full auth here
@app.route("/v1/tapi/trips", methods=['POST'])
def flask_lyft_tapi_trips_v1():
    # Handle any special Flask based request
    lyft_trip_data = flask.request.json

    lyft_response = lyft_trip_request(lyft_trip_data)

    return lyft_response
    # Need to also build exceptions to 400 Bad Request and 404 Not Found
    
# Some Authentication Wrapper Here
@app.route("/v1/tapi/trips/<trip_id>", methods=['PUT'])
def lyft_tapi_trips_v1_update(trip_id):
    lyft_trip_data = flask.request.json
    # Lyft will send similar data
    # Via needs to "request to update a booked ride" and then update??
    # Do we even need this!?!?
    lyft_response = lyft_update_request(lyft_trip_data)
    return lyft_response
    # Need to also build exceptions to 400 Bad Request and 404 Not Found

# Some Authentication Wrapper Here
@app.route("/v1/tapi/trips/<trip_id>/cancel", methods=['POST'])
def lyft_tapi_trips_v1_cancel(trip_id):
    # Find the translation between lyft's trip_id and via's trip_id
    lyft_cancel_request(trip_id)
    return "", 204
    # Need to also build exceptions to 400 Bad Request and 404 Not Found

@app.route("/connector", methods=['POST'])
def kiosk_via_request():
    via_trip_data = flask.request.json
    # Find the translation between lyft's trip_id and via's trip_id
    via_response = via_request_trip(via_trip_data)
    return via_response
    # Need to also build exceptions to 400 Bad Request and 404 Not Found
