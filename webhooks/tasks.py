from __future__ import absolute_import, unicode_literals

from celery import shared_task
from core.celery import app 
import time
from django.http import JsonResponse
from .models import WebhookEvent, Hl7LabRequest
from dhis2 import Api
import logging
from celery.utils.log import get_logger

logger = get_logger(__name__)

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
                message_body=message
            )

            logger.info(f"HL7 Message created for WebhookEvent ID {event_id}")
        else:
            logger.info(f"WebhookEvent ID {event_id} has not HMIS CODE")
        

    except WebhookEvent.DoesNotExist:
        logger.error(f"WebhookEvent with ID {event_id} does not exist")



@shared_task
def get_event_data(tei):
    api = Api('https://dev.eidsr.znphi.co.zm', 'Reuben_Kaponde', 'P@ssword#25$')
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


@shared_task
def get_hmis_code(orgUnit, tei):
    api = Api('https://dev.eidsr.znphi.co.zm', 'Reuben_Kaponde', 'P@ssword#25$')
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



