import azure.functions as func
import datetime
import json
import logging
import os
import gc
# import requests
import http.client
import urllib.parse
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
from opentelemetry.trace import SpanKind

# Configure OpenTelemetry for Application Insights
connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
if not connection_string:
    raise ValueError("APPLICATIONINSIGHTS_CONNECTION_STRING is not set")

# Initialize tracer provider
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Azure Monitor exporter
exporter = AzureMonitorTraceExporter(connection_string=connection_string)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))

# Static Application Insights client for logging
class AppInsightsClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppInsightsClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def log_info(self, message):
        self.logger.info(message)
        with tracer.start_as_current_span("trace", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("log.severity", "INFO")
            span.set_attribute("log.message", message)

    def log_warning(self, message):
        self.logger.warning(message)
        with tracer.start_as_current_span("trace", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("log.severity", "WARNING")
            span.set_attribute("log.message", message)

    def log_error(self, message):
        self.logger.error(message)
        with tracer.start_as_current_span("trace", kind=SpanKind.INTERNAL) as span:
            span.set_attribute("log.severity", "ERROR")
            span.set_attribute("log.message", message)

# Initialize the static client
app_insights_client = AppInsightsClient()

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
    # array_size = len(DataStore.static_data)
    logging.info(f"Added 1MB to static array. Current size: {len(DataStore.static_data)} bytes")

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    # # Prepare JSON payload for outbound POST request
    # payload = {
    #     "timestamp": datetime.datetime.utcnow().isoformat(),
    #     "name": name if name else "No name provided"
    # }
    # payload_json = json.dumps(payload)

    # # Make outbound HTTP POST request using http.client
    # try:
    #     # Parse the URL
    #     parsed_url = urllib.parse.urlparse("https://testpython56apim.azure-api.net/testpythonfa5602fa/http1")
    #     conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=5)
        
    #     # Set headers
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Content-Length": str(len(payload_json))
    #     }
        
    #     # Send POST request
    #     conn.request("POST", parsed_url.path, body=payload_json, headers=headers)
        
    #     # Get response
    #     response = conn.getresponse()
    #     status_code = response.status
    #     conn.close()
        
    #     logging.info(f"Outbound POST request sent. Status code: {status_code}")
    # except http.client.HTTPException as e:
    #     logging.error(f"Failed to send outbound POST request: {str(e)}")

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
    

# ================================================
# ================================================

@app.timer_trigger(schedule="0 * * * * *", arg_name="timer", run_on_startup=False, use_monitor=False)
def cleanup_timer(timer: func.TimerRequest) -> None:
    logging.info('Timer trigger function executed for cleanup.')
    # Clear the bytearray and force garbage collection
    DataStore.static_data.clear()
    gc.collect()
    logging.info('Static array cleared and garbage collection triggered.')

@app.route(route="http2", auth_level=func.AuthLevel.ANONYMOUS)
def http2(req: func.HttpRequest) -> func.HttpResponse:
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

    app_insights_client.log_info("Starting Request")

    # Make outbound HTTP POST request using http.client
    try:
        # Parse the URL
        parsed_url = urllib.parse.urlparse("https://testpython56apim.azure-api.net/testpythonfa5602fa/http1")
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
        app_insights_client.log_info(status_code)
        conn.close()
        
        logging.info(f"Outbound POST request sent. Status code: {status_code}")
    except http.client.HTTPException as e:
        logging.error(f"Failed to send outbound POST request: {str(e)}")

    app_insights_client.log_info("Completing Request")

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )