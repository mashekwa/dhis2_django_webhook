from django.contrib import admin
from .models import WebhookEvent, Dhis2Config,Hl7LabRequest

# Register your models here.
admin.site.register(WebhookEvent)
admin.site.register(Dhis2Config)
admin.site.register(Hl7LabRequest)
