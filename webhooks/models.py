from django.db import models

class Dhis2Config(models.Model):
    name = models.CharField(max_length=100, help_text="Configuration name (e.g., 'Primary DHIS2')", unique=True)
    api_url = models.URLField(help_text="Base URL for the DHIS2 API")
    username = models.CharField(max_length=100, help_text="DHIS2 Username")
    password = models.CharField(max_length=100, help_text="DHIS2 Password")
    is_active = models.BooleanField(default=True, help_text="Use this configuration if active")

    def __str__(self):
        return self.name
    
class KafkaConfig(models.Model):
    name = models.CharField(max_length=100, help_text="Configuration name (e.g., 'MOH Kafka')", unique=True)
    bootstrap_servers = models.CharField(max_length=100, help_text="Kafka Username")
    security_protocol = models.CharField(max_length=100, help_text="Kafka Username")
    mechanism = models.CharField(max_length=100, help_text="Kafka Username")
    username = models.CharField(max_length=100, help_text="Kafka Username")
    password = models.CharField(max_length=100, help_text="Kafka Password")
    group_id = models.CharField(max_length=100, help_text="Group ID")
    debug  = models.CharField(max_length=100, help_text="Kafka Password", null=True, blank=True)
    log_level = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Use this configuration if active")

    def __str__(self):
        return self.name

# Create your models here.
class WebhookEvent(models.Model):    
    tracked_entity_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    enrollment_id = models.CharField(max_length=50, null=True, blank=True)
    event_org_unit_id = models.CharField(max_length=50, null=True, blank=True)
    org_unit_code  = models.CharField(max_length=20, null=True, blank=True)
    program_stage_name = models.CharField(max_length=100, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    hmis_code = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    nmc_case_id = models.CharField(max_length=100, null=True, blank=True)
    nmc_order_id = models.CharField(max_length=100, null=True, blank=True)
    nmc_diag_name = models.CharField(max_length=100, null=True, blank=True)
    case_last_name = models.CharField(max_length=100, null=True, blank=True)
    case_first_name = models.CharField(max_length=100, null=True, blank=True)
    case_dob = models.CharField(max_length=100, null=True, blank=True)
    case_sex = models.CharField(max_length=100, null=True, blank=True)
    case_phone_number = models.CharField(max_length=100, null=True, blank=True)
    case_loinc_code = models.CharField(max_length=100, null=True, blank=True)
    case_loinc_name = models.CharField(max_length=100, null=True, blank=True)
    case_notifier_name = models.CharField(max_length=100, null=True, blank=True)
    case_specimen_name = models.CharField(max_length=100, null=True, blank=True)
    case_disease_code = models.CharField(max_length=50, null=True, blank=True)
    case_rapid_test_done = models.CharField(max_length=50, null=True, blank=True)
    case_notifier_designation = models.CharField(max_length=50, null=True, blank=True)
    patient_symptomatic = models.CharField(max_length=100, null=True, blank=True)
    lab_notifier_name = models.CharField(max_length=100, null=True, blank=True)
    lab_specimen_sent_date = models.CharField(max_length=100, null=True, blank=True)
    lab_specimen_collection_date = models.CharField(max_length=100, null=True, blank=True)
    lab_code = models.CharField(max_length=100, null=True, blank=True)
    facility_name = models.CharField(max_length=100, null=True, blank=True)
    lab_request_pathogen = models.CharField(max_length=100, null=True, blank=True)
    lab_filler_phone_number = models.CharField(max_length=20, null=True, blank=True)
    message_type = models.CharField(max_length=100, null=True, blank=True)
    message_uuid = models.CharField(max_length=100, null=True, blank=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    event_status = models.CharField(max_length=50, null=True, blank=True)
    raw_data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    posted_to_kafka = models.BooleanField(default=False)
    date_kafka_processed = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.case_first_name} {self.case_last_name} ({self.tracked_entity_id}/{self.nmc_order_id}) - {self.event_status}"
    


class Hl7LabRequest(models.Model):
    nmc_order_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    webhook = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE)    
    message_body=models.TextField(blank=True, null=True)
    event_status=models.CharField(max_length=50, null=True, blank=True)
    posted_to_kafka=models.CharField(max_length=50, null=True, blank=True)
