from celery_app import celery  # Import from celery_app.py
from celery import shared_task
#from .utils import get_data, post_data_api, normalize_to_short_date, util_lists_to_dict
from utils import send_telegram_message
import logging
import hl7
import csv
import os
from datetime import datetime
import requests
from decouple import config

logger = logging.getLogger(__name__)

@shared_task
def process_lab_results(lab_result):
    logger.info(f"Processing lab result: {lab_result}")
    # Add your processing logic here (e.g., saving to database, etc.)
    print(f"Lab result processed: {lab_result}")

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lab_result_{timestamp}.csv"

    # Ensure the directory exists (optional step)
    output_dir = "lab_results"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    # Write the lab_result to the CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Assuming lab_result is a dictionary, write header and values
        if isinstance(lab_result, dict):
            writer.writerow(lab_result.keys())  # Write the header
            writer.writerow(lab_result.values())  # Write the data
        else:
            writer.writerow(["Lab Result"])  # Generic header if not a dict
            writer.writerow([lab_result])  # Write the lab result

    print(f"Lab result processed and saved to {file_path}")


# TELEGRAM BOT CONFIG AND FUNCTION:
telegram_bot_token = config("TELEGRAM_BOT_TOKEN")

@shared_task
def send_telegram_message(user_id, message):    
    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        'chat_id': user_id,
        'text': message
    }

    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Error: {response.text}")

# Default payload template
# events_payload_default = {
#     "events": [
#         {
#             "trackedEntityInstance": "",
#             "program": "gr3uWZVzPQT",
#             "programStage": "mLzLxeatZRN",
#             "orgUnit": "",
#             "notes": [],
#             "dataValues": [
#                 {"dataElement": "uxSeYovVJTS", "value": "", "providedElsewhere": "false"},
#                 {"dataElement": "Zzldr5LQVk8", "value": "", "providedElsewhere": "false"},
#                 {"dataElement": "ahoi8aIMKjx", "value": "", "providedElsewhere": "false"},
#                 {"dataElement": "BsPzMEjoRYo", "value": "", "providedElsewhere": "false"},
#                 {"dataElement": "TnLQqhBvHTb", "value": "false", "providedElsewhere": "false"}
#             ],
#             "status": "COMPLETED",
#             "eventDate": ""
#         }
#     ]
# }

# @shared_task
# def normalize_message(hl7_message):
#     """Parse HL7 message and extract relevant fields."""
#     h = hl7.parse(hl7_message)
#     orc_segment = h['ORC']
#     msh_segment = h['MSH']
#     obr_segment = h['OBR']
#     obx_segment = h['OBX']

#     return {
#         "nmc_orderid": orc_segment[0][2][0],
#         "lab_location_code": msh_segment[0][4][0][1][0],
#         "hmis_code": msh_segment[0][6][0],
#         "lab_reference_num": orc_segment[0][3][0],
#         "lab_specimen_type": obr_segment[0][15][0][2][0],
#         "loinc_test_name": obr_segment[0][4][0][1][0],
#         "first_lab_result": obx_segment[1][5][0],
#         "results_released_date": obr_segment[0][22][0]
#     }

# @shared_task
# def transform_to_dhis_message(normalized_results):
#     """Fetch tracked entity and build DHIS2 payload."""
#     endpoint = (
#         f"/api/trackedEntityInstances/query.json"
#         f"?ou=PS5JpkoHHio&ouMode=ACCESSIBLE&program=gr3uWZVzPQT"
#         f"&attribute=w0JLuyVBnhf:EQ:{normalized_results['nmc_orderid']}&paging=false"
#     )

#     tracked_entity = get_data(endpoint, 'zm_eidsr_conn')

#     if not tracked_entity['rows']:
#         raise ValueError("Tracked entity does not exist")

#     entity_dict = util_lists_to_dict(
#         [header['name'] for header in tracked_entity['headers']],
#         tracked_entity['rows'][0]
#     )

#     payload = events_payload_default.copy()
#     payload['events'][0].update({
#         "trackedEntityInstance": entity_dict['instance'],
#         "orgUnit": entity_dict['ou'],
#         "eventDate": normalize_to_short_date(normalized_results['results_released_date'])
#     })

#     return payload

# @shared_task
# def submit_to_dhis(payload):
#     """Submit the final payload to DHIS2 API."""
#     headers = {"Content-Type": "application/json"}
#     return post_data_api("/api/events", payload, headers, 'zm_eidsr_conn')