import azure.functions as func
import datetime
import json
import logging
import os
import gc

app = func.FunctionApp()

# Static array to store data (class-level variable)
class DataStore:
    static_data = bytearray()

@app.route(route="http1", auth_level=func.AuthLevel.ANONYMOUS)
def http1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Add 1MB of random data to static array
    ONE_MB = 1024 * 1024  # 1MB in bytes
    DataStore.static_data.extend(os.urandom(ONE_MB))
    logging.info(f"Added 1MB to static array. Current size: {len(DataStore.static_data)} bytes")

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

@app.timer_trigger(schedule="0 * * * * *", arg_name="timer", run_on_startup=False, use_monitor=False)
def cleanup_timer(timer: func.TimerRequest) -> None:
    logging.info('Timer trigger function executed for cleanup.')
    # Clear the bytearray and force garbage collection
    DataStore.static_data.clear()
    gc.collect()
    logging.info('Static array cleared and garbage collection triggered.')