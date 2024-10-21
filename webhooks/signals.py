from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import transform_request_to_hl7
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=WebhookEvent)
def trigger_hl7_message(sender, instance, **kwargs):
    if instance.event_status and instance.event_status.strip() == "COMPLETED":
        logger.info(f"Event with ID {instance.id} has status COMPLETED, triggering HL7 transformation.")
        transform_request_to_hl7.delay(instance.id)
    else:
        logger.info(f"Event with ID {instance.id} not eligible for HL7 transformation. Status: {instance.event_status}")


