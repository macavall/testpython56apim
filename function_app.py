import azure.functions as func
import datetime
import json
import logging
import os
import gc
# import requests
import http.client
import urllib.parse
import uuid
from azure.monitor.opentelemetry import configure_azure_monitor 
configure_azure_monitor()

app = func.FunctionApp()

# Static array to store data (class-level variable)
# class DataStore:
#     static_data = bytearray()

@app.route(route="http1/{guid_value:guid?}", auth_level=func.AuthLevel.ANONYMOUS)
def http1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    guid_value = req.route_params.get('guid_value')
    logging.info(guid_value)

    # Add 1MB of random data to static array
    # ONE_MB = 1024 * 1024  # 1MB in bytes
    # DataStore.static_data.extend(os.urandom(ONE_MB))
    # array_size = len(DataStore.static_data)
    # logging.info(f"Added 1MB to static array. Current size: {len(static_data)} bytes")

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    

# ================================================
# ================================================

# @app.timer_trigger(schedule="0 * * * * *", arg_name="timer", run_on_startup=False, use_monitor=False)
# def cleanup_timer(timer: func.TimerRequest) -> None:
#     logging.info('Timer trigger function executed for cleanup.')
#     # Clear the bytearray and force garbage collection
#     DataStore.static_data.clear()
#     gc.collect()
#     logging.info('Static array cleared and garbage collection triggered.')

@app.route(route="http2", auth_level=func.AuthLevel.ANONYMOUS)
def http2(req: func.HttpRequest, context) -> func.HttpResponse:

    # Get the invocation ID from the request headers
    invocation_id = context.invocation_id 
    log_extra = {"custom_dimensions": {"InvocationId": invocation_id}}
    # req.headers.get('x-ms-invocation-id')
    # logging.info(f'INVOCATION ID: {invocation_id}')
    logging.info(f'INVOCATION ID: {invocation_id}', extra=log_extra)
    
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    # Prepare JSON payload for outbound POST request
    payload = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "name": name if name else "No name provided"
    }
    payload_json = json.dumps(payload)

    logging.info(f"Starting Request {invocation_id}")



    # Make outbound HTTP POST request using http.client
    try:
        # Parse the URL
        random_guid = str(uuid.uuid4())
        logging.info(random_guid)
        parsed_url = urllib.parse.urlparse("https://testpython56apim.azure-api.net/testpythonfa5602fa/http1/" + random_guid)
        conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=5)
        
        # Set headers
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(payload_json))
        }
        
        # Send POST request
        conn.request("POST", parsed_url.path, body=payload_json, headers=headers)
        
        # Get response
        response = conn.getresponse()
        status_code = response.status
        logging.info(status_code)
        conn.close()
        
        logging.info(f"Outbound POST request sent. Status code: {status_code}")
    except http.client.HTTPException as e:
        logging.error(f"Failed to send outbound POST request: {str(e)}")

    logging.info(f"Completing Request {invocation_id}")

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )