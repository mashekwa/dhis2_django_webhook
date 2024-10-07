from django.contrib import admin
from .models import WebhookEvent, Dhis2Config

# Register your models here.
admin.site.register(WebhookEvent)
admin.site.register(Dhis2Config)
