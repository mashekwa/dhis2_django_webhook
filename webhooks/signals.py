from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import transform_request_to_hl7, send_kafka_message
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=WebhookEvent)
def trigger_hl7_message(sender, instance, created, **kwargs):
    logger.info(f"****-------TRANSFORMER-------********")
    if instance.hmis_code and instance.event_status.strip() == "COMPLETED":
        logger.info(f"ID: {instance.id} has status COMPLETED, triggering HL7 transformation.")
        transform_request_to_hl7.delay(instance.id)
    else:
        logger.info(f"ID: {instance.id} not eligible for HL7 transformation. Status: {instance.event_status}")


# @receiver(post_save, sender=Hl7LabRequest)
# def post_to_kafka(sender, instance, created, **kwargs):
#     """Signal to trigger Kafka message upon HL7LabRequest creation or update."""
#     if instance.message_body and instance.event_status == "COMPLETED":
#         logger.info(f"Event with ID {instance.id} has status COMPLETED, posting to KAFKA.")
#         send_kafka_message.delay(instance.id)  # Send ID to Celery task for processing
#     else:
#         logger.info(f"Event with ID {instance.id} Not Posting to KAFKA. Status: {instance.event_status}")


