from django.db import models

class Dhis2Config(models.Model):
    instance_name = models.CharField(max_length=50, null=True, blank=True)
    base_url = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Configs for: {self.instance_name}"

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
    webhook = models.ForeignKey(WebhookEvent, on_delete=models.CASCADE)
    nmc_order_id = models.CharField(max_length=100, null=True, blank=True)
    message_body=models.TextField(blank=True, null=True)
    event_status=models.CharField(max_length=50, null=True, blank=True)
    posted_to_kafka=models.CharField(max_length=50, null=True, blank=True)
