from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .tasks import transform_request_to_hl7


@receiver(post_save, sender=WebhookEvent)
def trigger_hl7_message(sender, instance, **kwargs):
    # Check if both event_status and hmis_code are not null
    if instance.event_status == "COMPLETED":
        transform_request_to_hl7.delay(instance.id)


