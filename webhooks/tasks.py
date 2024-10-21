from __future__ import absolute_import, unicode_literals

from celery import shared_task
from core.celery import app 
import time
from django.http import JsonResponse
from .models import WebhookEvent, Hl7LabRequest
from dhis2 import Api
import logging
from celery.utils.log import get_logger
from confluent_kafka import Producer, KafkaException
from django.db import transaction
from django.conf import settings
import uuid

logger = get_logger(__name__)

# Initialize Kafka producer with the configuration, configs in settings .py. and .env file
producer = Producer(settings.KAFKA_CONFIG)
message_uuid = str(uuid.uuid4())

def delivery_report(err, msg, hl7_request_id):
    """Callback to log the delivery result and update the database."""
    try:
        with transaction.atomic():
            hl7_request = Hl7LabRequest.objects.get(id=hl7_request_id)

            if err is not None:
                logger.error(f"Message delivery failed: {err}")
                hl7_request.posted_to_kafka = "failed"
            else:
                logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
                hl7_request.posted_to_kafka = "success"

            hl7_request.save()

    except Hl7LabRequest.DoesNotExist:
        logger.error(f"HL7LabRequest with ID {hl7_request_id} does not exist.")
    except Exception as e:
        logger.error(f"Error updating Kafka status: {e}")


@shared_task
def send_kafka_message(hl7_msg, hl7_request_id):
    """Send an HL7 message to Kafka asynchronously."""
    try:
        logger.info(f"Sending message to Kafka: {hl7_msg}")

        # Produce the message to the Kafka topic "eidsr-orders"
        producer.produce(
            "eidsr-orders",
            value=hl7_msg,
            callback=lambda err, msg: delivery_report(err, msg, hl7_request_id)
        )
        producer.poll(1)  # Wait up to 1 second for delivery callback
        producer.flush()

    except KafkaException as ke:
        logger.error(f"Kafka error: {ke.args}")
    except Exception as e:
        logger.error(f"Failed to send message to Kafka: {e}")



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
            Hl7LabRequest.objects.create(
                webhook=webhook_event,
                nmc_order_id=webhook_event.nmc_order_id,
                message_body=message,
                event_status=webhook_event.event_status
            )

            logger.info(f"HL7 Message created for WebhookEvent ID {event_id} |NMC_ORDER_ID: {webhook_event.nmc_order_id} ")
        else:
            logger.info(f"WebhookEvent ID {event_id} has not HMIS CODE")
        

    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent with ID {event_id} does not exist")



@shared_task
def get_event_data(tei):
    api = Api(settings.DHIS_URL, settings.DHIS_USER, settings.DHIS_PASS)
    params = {
        'trackedEntity': tei,
        'fields': 'event,status, trackedEntity',
    }
    r = api.get('tracker/events', params=params)
    data = r.json()['instances']

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
    api = Api(settings.DHIS_URL, settings.DHIS_USER, settings.DHIS_PASS)
    params = {
        'fields': 'attributeValues[value]',
        'filter': 'attributeValues.attribute.id:eq:ZpAtPLnerqC'
    }
    ou = api.get(f'organisationUnits/{orgUnit}', params=params)
    data = ou.json()

    hmis_code = None
    if 'attributeValues' in data and data['attributeValues']:
        hmis_code = data['attributeValues'][0].get('value')

    if hmis_code:
        WebhookEvent.objects.filter(tracked_entity_id=tei).update(hmis_code=hmis_code)

    return hmis_code




