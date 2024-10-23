from django.contrib import admin
from .models import WebhookEvent, Dhis2Config,Hl7LabRequest, KafkaConfig

# Register your models here.
admin.site.register(WebhookEvent)
@admin.register(KafkaConfig)
class KafkaConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'bootstrap_servers', 'security_protocol', 'is_active']
    list_filter = ['is_active']
    search_fields = ['bootstrap_servers']

@admin.register(Dhis2Config)
class Dhis2ConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'api_url', 'is_active']
    list_filter = ['is_active']
    search_fields = ['api_url']

admin.site.register(Hl7LabRequest)

