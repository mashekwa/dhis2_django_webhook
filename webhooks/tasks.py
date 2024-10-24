from __future__ import absolute_import, unicode_literals
from decouple import config
from celery import shared_task
from core.celery import app 
import urllib3
import time
from django.http import JsonResponse
from .models import WebhookEvent, Hl7LabRequest
from dhis2 import Api
import logging
from celery.utils.log import get_logger
from confluent_kafka import Producer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from django.db import transaction
from django.conf import settings
import uuid
import pandas as pd
import os 
import re

logger = get_logger(__name__)

# Suppress only InsecureRequestWarnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

KAFKA_CONFIG = {
    "bootstrap.servers": config("KAFKA_BOOTSTRAP_SERVERS"),
    "security.protocol": config("KAFKA_SECURITY_PROTOCOL"),
    "sasl.mechanism": config("KAFKA_SASL_MECHANISM"),
    "sasl.username": config("KAFKA_USERNAME"),
    "sasl.password": config("KAFKA_PASSWORD"),
    "group.id": config("KAFKA_GROUP_ID"),
    'socket.timeout.ms': 30000,  # Increase to 30 seconds
    'message.timeout.ms': 30000,  # Increase to 30 seconds
    'retries': 5,  # Retry sending the message
    'debug': 'all',
    'client.id': 'znphi-producer',
    'acks': 'all',  # Ensure all replicas acknowledge
}

def create_kafka_topic(topic_name, num_partitions=1, replication_factor=1):
    """Create a Kafka topic if it doesn't exist."""
    admin_client = AdminClient(KAFKA_CONFIG)

    # Check if the topic already exists
    topic_metadata = admin_client.list_topics(timeout=10)
    if topic_name in topic_metadata.topics:
        logger.info(f"Topic '{topic_name}' already exists.")
        return {"status": "exists", "message": f"Topic '{topic_name}' already exists."}

    # Create a new topic with the specified configuration
    new_topic = NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
    try:
        # Asynchronous topic creation
        admin_client.create_topics([new_topic])
        logger.info(f"Topic '{topic_name}' created successfully.")
        return {"status": "success", "message": f"Topic '{topic_name}' created successfully."}
    except Exception as e:
        logger.error(f"Failed to create topic '{topic_name}': {e}")
        return {"status": "failed", "reason": str(e)}

# Initialize Kafka producer with the configuration, configs in settings .py. and .env file
producer = Producer(KAFKA_CONFIG)
message_uuid = str(uuid.uuid4())
dhis_user = config('DHIS_USER')
dhis_pass = config('DHIS_PASS')
dhis_url = config('DHIS_URL')

# def delivery_report(err, msg, hl7_request_id):
#     """Callback to log the delivery result and update the database."""
#     try:
#         with transaction.atomic():
#             hl7_request = Hl7LabRequest.objects.get(id=hl7_request_id)

#             if err is not None:
#                 logger.error(f"Message delivery failed: {err}")
#                 hl7_request.posted_to_kafka = "failed"
#             else:
#                 logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
#                 hl7_request.posted_to_kafka = "success"

#             hl7_request.save()

#     except Hl7LabRequest.DoesNotExist:
#         logger.error(f"HL7LabRequest with ID {hl7_request_id} does not exist.")
#     except Exception as e:
#         logger.error(f"Error updating Kafka status: {e}")
        

# PHONE FORMAT HELPER FUNCTION
def format_phone_number(phone_number):
    """Format the phone number into (260)XXXX format."""
    if not phone_number:
        return ""

    if len(phone_number) == 12:
        return f"(260){phone_number[3:]}"
    elif len(phone_number) == 10:
        return f"(260){phone_number[1:]}"
    return phone_number  # Return as-is if it doesn't match expected patterns

def normalize_to_hl7_date(date_string) -> str:
    result = re.sub(r'-', '', date_string)
    return result


def normalize_to_hl7_datetime(date_time_string) -> str:
    result = re.sub(r'[-T\:]+', '', date_time_string)
    return result


def isnan(value):
    try:
        import math
        return math.isnan(float(value))
    except:
        return False    


# SPECIMENT NAME HELPER FUNCTION
def get_real_speciment(LAB_SPEC_TYPE):
    specimen_type_filename = os.path.join(os.path.dirname(__file__), 'mappings', 'lab_specimen_type.csv')
    specimen_type_df = pd.read_csv(specimen_type_filename)

    # Filter and assign
    is_specimen = specimen_type_df['code'] == LAB_SPEC_TYPE
    specimen_filter = specimen_type_df[is_specimen]
    if specimen_filter.shape[0] > 0:
        case_specimen_name = specimen_filter['name'].to_string(index = False)
    else:
        case_specimen_name = LAB_SPEC_TYPE

    return case_specimen_name



# @shared_task
# def send_kafka_message(hl7_msg, hl7_request_id):
#     """Send an HL7 message to Kafka asynchronously."""
#     logger.info(f"***-----KAFKA MESSAGE SENDING------****")
#     try:
#         logger.info(f"Sending message to Kafka: {hl7_msg}")

#         # Produce the message to the Kafka topic "eidsr-orders"
#         producer.produce(
#             "eidsr-orders",
#             value=hl7_msg,
#             callback=lambda err, msg: delivery_report(err, msg, hl7_request_id)
#         )
#         producer.poll(1)  # Wait up to 1 second for delivery callback
#         producer.flush()
#         logger.info(f"***----KAFKA SENT---****")
#     except KafkaException as ke:
#         logger.error(f"Kafka error: {ke.args}")
#     except Exception as e:
#         logger.error(f"Failed to send message to Kafka: {e}")

# @shared_task
# def send_kafka_message(hl7_msg, hl7_request_id):
#     """Send an HL7 message to Kafka asynchronously."""  
#     try:
#         # Check if Kafka is reachable by fetching metadata
#         metadata = producer.list_topics(timeout=10)  # Timeout after 5 seconds
#         logger.info(f"Kafka connection successful. Available topics: {metadata.topics.keys()}")

#         logger.info(f"Sending message to Kafka: {hl7_msg}")

#         # Produce the message to the Kafka topic "eidsr-orders"
#         producer.produce(
#             "eidsr-orders",
#             value=hl7_msg,
#             callback=lambda err, msg: delivery_report(err, msg, hl7_request_id)
#         )
#         producer.poll(1)  # Wait up to 1 second for delivery callback
#         producer.flush()
#         logger.info("***----KAFKA SENT---****")
    
#     except KafkaException as ke:
#         logger.error(f"Kafka error: {ke.args}")
#     except Exception as e:
#         logger.error(f"Failed to send message to Kafka: {e}")
# def delivery_report(err, msg, hl7_request_id):
#     """Delivery callback to handle message success or failure."""
#     if err is not None:
#         logger.error(f"Message delivery failed for request {hl7_request_id}: {err}")
#     else:
#         logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


# @shared_task(bind=True)  # Bind=True allows access to 'self' for task info
# def send_kafka_message(self, hl7_request_id):
#     """Send an HL7 message to Kafka asynchronously and return status."""
#     logger.info(f"*******----SEND KAFKA MSG----*****")
#     logger.info(f"****** \n{KAFKA_CONFIG} \n*******")
#     hl7_request = Hl7LabRequest.objects.get(id=hl7_request_id)
#     logger.info(f"Sending message to Kafka: \n{hl7_request.message_body}")
#     try:
#         # Verify Kafka connection by fetching metadata
#         metadata = producer.list_topics(timeout=10)
#         if "eidsr-orders" not in metadata.topics:
#             logger.error("Kafka topic 'eidsr-orders' not found.")
#             return {"status": "failed", "reason": "Topic not found"}

#         logger.info(f"Kafka connection successful. Available topics: {metadata.topics.keys()}")
        
#         logger.info(f"Sending message to Kafka: {hl7_request.message_body}")
#         # Produce the message to the Kafka topic "eidsr-orders"
#         producer.produce(
#             bytes('eidsr-orders', encoding="utf-8"),
#             value=bytes(hl7_request.message_body, encoding="utf-8")
#             callback=lambda err, msg: delivery_report(err, msg, hl7_request_id)
#         )

#         # Ensure the message is sent by polling and flushing
#         producer.poll(1)  # Non-blocking poll to trigger delivery callbacks
#         producer.flush(timeout=10)  # Wait up to 10 seconds for message delivery

#         logger.info("***----KAFKA SENT---****")
#         return {"status": "success", "message": "Message sent to Kafka"}

#     except KafkaException as ke:
#         logger.error(f"Kafka error: {ke.args}")
#         return {"status": "failed", "reason": str(ke.args)}

#     except Exception as e:
#         logger.error(f"Failed to send message to Kafka: {e}")
#         return {"status": "failed", "reason": str(e)}


def delivery_report(err, msg, hl7_request_id):
    """Callback function to report message delivery status."""
    if err is not None:
        logger.error(f"Message delivery for {hl7_request_id} failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

@shared_task(bind=True)
def send_kafka_message(self, hl7_request_id):
    """
    Send an HL7 message to Kafka asynchronously and return status.
    This task fetches the message from the database.
    """
    logger.info("*******----SEND KAFKA MSG----*****")
    logger.info(f"Kafka Configuration: {KAFKA_CONFIG}")
    logger.info(f"\n")
    topic = 'eidsr-orders'

    try:
        # Ensure topic exists (or create if needed)
        create_kafka_topic(topic)

        # Fetch HL7 message from the database
        hl7_request = Hl7LabRequest.objects.get(id=hl7_request_id)
        hl7_msg = hl7_request.message_body.encode('utf-8')
        

        logger.info(f"Sending message to Kafka: \n{hl7_request.message_body}")

        # Verify Kafka broker connectivity
        metadata = producer.list_topics(timeout=10)
        if topic not in metadata.topics:
            logger.error(f"Kafka topic '{topic}' not found.")
            return {"status": "failed", "reason": "Topic not found"}

        logger.info(f"Kafka connection successful. Available topics: {metadata.topics.keys()}")

        # Produce the message to Kafka
        producer.produce(
            topic=topic,
            value=hl7_msg,
            callback=lambda err, msg: delivery_report(err, msg, hl7_request_id)
        )

        # Ensure the message is delivered
        producer.poll(1)  # Non-blocking poll to trigger delivery callbacks
        producer.flush(timeout=30)  # Wait up to 10 seconds for delivery

        logger.info("***----KAFKA SENT---****")
        return {"status": "success", "message": "Message sent to Kafka"}

    except Hl7LabRequest.DoesNotExist:
        logger.error(f"HL7 request with ID {hl7_request_id} not found.")
        return {"status": "failed", "reason": "HL7 request not found"}

    except KafkaException as ke:
        logger.error(f"Kafka error: {ke.args}")
        return {"status": "failed", "reason": str(ke.args)}

    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}", exc_info=True)
        return {"status": "failed", "reason": str(e)}



@shared_task
def transform_request_to_hl7(event_id):
    try:
        # Fetch the WebhookEvent object by the provided event_id
        webhook_event = WebhookEvent.objects.get(id=event_id)

        # Ensure both event_status and hmis_code are not null
        if webhook_event.hmis_code:
            # Mapping the HL7 Message

            message = (
                f'MSH|^~\\&|ZMeIDSR|^{webhook_event.hmis_code}^L|DISA*LAB|{webhook_event.lab_code}|'
                f'{webhook_event.lab_specimen_sent_date}||{webhook_event.message_type}|{webhook_event.message_uuid}|'
                f'T^T|2.5|||||{webhook_event.country}\r'
                f'PID|1||{webhook_event.nmc_case_id}^^^^||{webhook_event.case_last_name}^{webhook_event.case_first_name}||'
                f'{webhook_event.case_dob}|{webhook_event.case_sex[0:1]}|||||{webhook_event.case_phone_number}|||||||||||||||||\r'
                f'PV1|1|^N|{webhook_event.hmis_code}^^^SPC52|||||^{webhook_event.lab_notifier_name}\r'
                f'ORC|NW|{webhook_event.nmc_order_id}^EIDSR|||IP||||{webhook_event.lab_specimen_sent_date}|||^^^^^^^^^^^^^^^'
                f'{webhook_event.lab_notifier_name}||||P^^EIDSR|||||{webhook_event.facility_name}^{webhook_event.hmis_code}\r'
                f'OBR|1|{webhook_event.nmc_order_id}^EIDSR||{webhook_event.case_loinc_code}^{webhook_event.case_loinc_name}'
                f'^LN^^|||{webhook_event.lab_specimen_sent_date}||||O||{webhook_event.nmc_diag_name}||'
                f'{webhook_event.case_specimen_name}|^{webhook_event.lab_notifier_name}\r'
                f'DG1|1||{webhook_event.lab_request_pathogen}^{webhook_event.nmc_diag_name}^I10|||F\r'
                f'SPM|1|||{webhook_event.case_specimen_name}^{webhook_event.case_specimen_name}|||||||||||||'
                f'{webhook_event.lab_specimen_collection_date}|{webhook_event.lab_specimen_collection_date}\r'
            )

            # Create Hl7LabRequest object to store the generated HL7 message
            event, created = Hl7LabRequest.objects.update_or_create(
                nmc_order_id=webhook_event.nmc_order_id,
                defaults={
                    'webhook':webhook_event,
                    'message_body':message,
                    'event_status':webhook_event.event_status
                }
            )

            # Hl7LabRequest.objects.create(
            #     webhook=webhook_event,
            #     nmc_order_id=webhook_event.nmc_order_id,
            #     message_body=message,
            #     event_status=webhook_event.event_status
            # )
            if created:
                logger.info(f"HL7 Message created for WebhookEvent ID {event_id} |NMC_ORDER_ID: {webhook_event.nmc_order_id} ")
            else:
                logger.info(f"HL7 Message updated for WebhookEvent ID {event_id} |NMC_ORDER_ID: {webhook_event.nmc_order_id} ")

            logger.info(f"HL7 Message processing complete! ")
            logger.info(f"{event.id}")
            #send_kafka_message(event.id)
        else:
            logger.info(f"WebhookEvent ID {event_id} has not HMIS CODE")        

    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent with ID {event_id} does not exist")



@shared_task
def get_event_data(tei):
    logger.info(f"DHIS_URL: {dhis_url}")
    api = Api(f"{dhis_url}", dhis_user, dhis_pass)    
    api.session.verify = False  # Disable SSL verification by modifying the internal session
    params = {
        'trackedEntity': tei,
        'fields': 'event,status, trackedEntity',
    }    

    try:
        r = api.get('tracker/events', params=params)
        data = r.json()['instances']
        r.raise_for_status()
        logger.info(r)
    except api.ClientException as e:
        print(f"Request failed: {e}")
    except api.RequestException as dhis_error:
        print(f"DHIS2 API error: {dhis_error.code}, {dhis_error.url}, {dhis_error.description}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

    if data:
        first_item = data[0]
        event = first_item.get('event')
        status = first_item.get('status')
        tei = first_item.get('trackedEntity')
        WebhookEvent.objects.filter(tracked_entity_id=tei).update(
            event_id=event,
            event_status=status
        )

    return status


@shared_task
def get_hmis_code(orgUnit, tei):
    logger.info(f"DHIS_URL: {dhis_url}")
    api = Api(f"{dhis_url}", dhis_user, dhis_pass)    
    api.session.verify = False  # Disable SSL verification by modifying the internal session
    params = {
        'fields': 'attributeValues[value]',
        'filter': 'attributeValues.attribute.id:eq:ZpAtPLnerqC'
    }

    try:
        ou = api.get(f'organisationUnits/{orgUnit}', params=params)
        data = ou.json()
        ou.raise_for_status()
        logger.info(ou)
    except api.ClientException as e:
        print(f"Request failed: {e}")
    except api.RequestException as dhis_error:
        print(f"DHIS2 API error: {dhis_error.code}, {dhis_error.url}, {dhis_error.description}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

    hmis_code = None
    if 'attributeValues' in data and data['attributeValues']:
        hmis_code = data['attributeValues'][0].get('value')

    if hmis_code:
        WebhookEvent.objects.filter(tracked_entity_id=tei).update(hmis_code=hmis_code)

    return hmis_code

@shared_task
def process_webhook_data(json_data):
    """Process the received webhook data."""
    try:
        # Extracting the necessary fields from the parsed JSON
        tracked_entity_id = json_data.get('TRACKED_ENTITY_ID', None)
        enrollment_id = json_data.get('ENROLLMENT_ID', None)
        event_org_unit_id = json_data.get('EVENT_ORG_UNIT_ID', None)
        org_unit_code = json_data.get('ORG_UNIT_CODE', None)
        facility_name = json_data.get('ORG_UNIT_NAME', None)
        program_stage_name = json_data.get('PROGRAM_STAGE_NAME', None)
        event_date = json_data.get('EVENT_DATE', None)
        nmc_case_id  = json_data.get('RcCp8T4IWfS', None)
        nmc_order_id = json_data.get('w0JLuyVBnhf', None)
        nmc_diag_name = json_data.get('iSIhKjnlMkv', None)
        case_last_name = json_data.get('ENRjVGxVL6l', None)
        case_first_name = json_data.get('VRrev6t48AR', None)
        case_dob = json_data.get('MG13HhvitMm', None)
        case_sex = json_data.get('aBWXXTLYXGc', None)
        case_age_days = json_data.get('XIZZPCv7ljB', None)        
        case_phone_number = json_data.get('LAJ1gDQ6Mrz', None)
        case_phone_number_formatted = format_phone_number(case_phone_number) # USE HELPER FUNCTION TO FORMAT PHONE
        case_loinc_code = json_data.get('slkkXAIqOnm', None)
        case_disease_code = json_data.get('iSIhKjnlMkv', None)
        case_rapid_test_done = json_data.get('nxNEeKHN6qP', None)
        if case_rapid_test_done is not None:
            case_rapid_test_done = case_rapid_test_done.split('_')[1]                
        case_notifier_name = json_data.get('JG8nmeI0wPM', None)
        case_notifier_designation = json_data.get('ldK0zmOre52', None)
        case_specimen_name = json_data.get('UEY5S9a1wAY', None)
        case_specimen_name = get_real_speciment(case_specimen_name) # USE MAPPING FOR CASE SPECIMEN NAME
        patient_symptomatic = json_data.get('TVNg8Gec4uT').split('_')[1]
        lab_notifier_name =  json_data.get('VMAxwiQtcIY', None)
        lab_specimen_sent_date =json_data.get('yZ2nW8FCIVg', None)
        lab_specimen_collection_date = json_data.get('XMvZglNvV2F', None)
        lab_filler_phone_number = json_data.get('KFxGykEGOQj', None)
        lab_filler_phone_number = format_phone_number(lab_filler_phone_number)
        lab_code = json_data.get('HhNhMHtKYiB')[-3:]
        lab_request_pathogen = json_data.get('nMuxTzmCz7U', None)
        case_loinc_name = "Culture" # WHY IS THIS CULTURE BY DEFAULT  

        # Create or update the WebhookEvent
        event, created = WebhookEvent.objects.update_or_create(
            tracked_entity_id=tracked_entity_id,
            defaults={
                'event_org_unit_id': event_org_unit_id,
                'org_unit_code': org_unit_code,
                'enrollment_id':enrollment_id,
                'program_stage_name': program_stage_name,
                'event_date': event_date,
                'nmc_case_id':nmc_case_id,
                'nmc_order_id':nmc_order_id,
                'case_last_name':case_last_name,
                'case_first_name':case_first_name,
                'case_dob': case_dob,
                'case_sex':case_sex ,
                'lab_code':lab_code,
                'patient_symptomatic':patient_symptomatic,
                'lab_notifier_name':lab_notifier_name,
                'facility_name':facility_name,
                'lab_request_pathogen':lab_request_pathogen,
                'raw_data': json_data,
                'message_type': 'OML^O21^OML_O21',
                'country':'ZMB',
                'nmc_diag_name':nmc_diag_name,
                'lab_filler_phone_number': lab_filler_phone_number,
                'case_phone_number':case_phone_number_formatted,
                'case_disease_code':case_disease_code,
                'case_loinc_code':case_loinc_code,
                'case_loinc_name':case_loinc_name,
                'lab_specimen_sent_date':lab_specimen_sent_date,
                'lab_specimen_collection_date':lab_specimen_collection_date,
                'case_rapid_test_done':case_rapid_test_done,
                'case_notifier_name':case_notifier_name,
                'case_notifier_designation': case_notifier_designation,
                'case_specimen_name':case_specimen_name,
            }
        )  
        # Trigger additional Celery tasks if necessary
        if created:
            print(f"{tracked_entity_id} created.")
        else:
            print(f"{tracked_entity_id} updated.")

        # Call background tasks asynchronously
        get_event_data.delay(tracked_entity_id)

        # Call get_hmis_code only if the hmis_code is missing
        if not event.hmis_code:
            get_hmis_code.delay(event_org_unit_id, tracked_entity_id)

    except Exception as e:
        # Log errors and handle exceptions gracefully
        print(f"Error processing webhook data: {str(e)}")