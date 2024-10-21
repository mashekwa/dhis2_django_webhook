from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from telegram import Bot
import os
from .models import WebhookEvent
from dhis2 import Api
from .tasks import get_event_data, get_hmis_code
import uuid

api = Api('https://dev.eidsr.znphi.co.zm', 'Reuben_Kaponde', 'P@ssword#25$')

TELEGRAM_BOT_TOKEN = '8000772138:AAHeb4zG9yKi0ZSBB_mCYoSE6zFjpa6bne8'
TELEGRAM_CHAT_ID = '1435205700'

def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Message sent to Telegram: {message}")
    except Exception as e:
        print(f"Failed to send message: {e}")



# FUNCTION to GET TEI using Attribute
nmc_no = "NMC_357282"
ou = "pXhz0PLiYZX"
program_id = 'gr3uWZVzPQT'
program_stage_id = 'GIFHpXo8dlP'

url= f"https://dev.eidsr.znphi.co.zm/api/trackedEntityInstances.json?program=gr3uWZVzPQT&ou={ou}&filter=RcCp8T4IWfS:eq:{nmc_no}"   


@csrf_exempt
def webhook_receiver(request):
    if request.method == 'POST':
        # Get the raw POST body (it can be JSON)
        raw_data = request.body.decode('utf-8')
        print(raw_data)
        
        try:
            # Parse the JSON data
            json_data = json.loads(raw_data)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        
        if json_data.get('HhNhMHtKYiB'):        
            # Extracting the necessary fields from the parsed JSON
            tracked_entity_id = json_data.get('TRACKED_ENTITY_ID', None)
            enrollment_id = json_data.get('ENROLLMENT_ID', None)
            event_org_unit_id = json_data.get('EVENT_ORG_UNIT_ID', None)
            org_unit_code = json_data.get('ORG_UNIT_CODE', None)
            facility_name = json_data.get('ORG_UNIT_NAME', None)
            program_stage_name = json_data.get('PROGRAM_STAGE_NAME', None)
            event_date = json_data.get('EVENT_DATE', None)
            nmc_case_id  = json_data.get('RcCp8T4IWfS', None)
            nmc_order_id = json_data.get('w0JLuyVBnhf', None)
            nmc_diag_name = json_data.get('iSIhKjnlMkv', None)
            case_last_name = json_data.get('ENRjVGxVL6l', None)
            case_first_name = json_data.get('VRrev6t48AR', None)
            case_dob = json_data.get('MG13HhvitMm', None)
            case_sex = json_data.get('aBWXXTLYXGc', None)
            case_age_days = json_data.get('XIZZPCv7ljB', None)        
            case_phone_number = json_data.get('LAJ1gDQ6Mrz', None)
            # Formatted contact
            case_phone_number_formatted = ""
            if len(case_phone_number) == 12:
                case_phone_number_formatted = "(260)" + case_phone_number[3:]
            elif len(case_phone_number) == 10:
                case_phone_number_formatted = "(260)" + case_phone_number[1:]
                
            case_loinc_code = json_data.get('slkkXAIqOnm', None)
            case_disease_code = json_data.get('iSIhKjnlMkv', None)
            case_rapid_test_done = json_data.get('nxNEeKHN6qP', None)
            if case_rapid_test_done is not None:
                case_rapid_test_done = case_rapid_test_done.split('_')[1]
                
            case_notifier_name = json_data.get('JG8nmeI0wPM', None)
            case_notifier_designation = json_data.get('ldK0zmOre52', None)
            case_specimen_name = json_data.get('UEY5S9a1wAY', None)
            patient_symptomatic = json_data.get('TVNg8Gec4uT').split('_')[1]
            lab_notifier_name =  json_data.get('VMAxwiQtcIY', None)
            lab_specimen_sent_date =json_data.get('yZ2nW8FCIVg', None)
            lab_specimen_collection_date = json_data.get('XMvZglNvV2F', None)
            lab_filler_phone_number = json_data.get('KFxGykEGOQj', None)
            lab_code = json_data.get('HhNhMHtKYiB')[-3:]
            lab_request_pathogen = json_data.get('nMuxTzmCz7U', None)
            case_loinc_name = "Culture" # WHY IS THIS CULTURE BY DEFAULT        
            
            try:
                # Use update_or_create to insert or update the entry
                event, created = WebhookEvent.objects.update_or_create(
                    tracked_entity_id=tracked_entity_id,
                    defaults={
                        'event_org_unit_id': event_org_unit_id,
                        'org_unit_code': org_unit_code,
                        'enrollment_id':enrollment_id,
                        'program_stage_name': program_stage_name,
                        'event_date': event_date,
                        'nmc_case_id':nmc_case_id,
                        'nmc_order_id':nmc_order_id,
                        'case_last_name':case_last_name,
                        'case_first_name':case_first_name,
                        'case_dob': case_dob,
                        'case_sex':case_sex ,
                        'lab_code':lab_code,
                        'patient_symptomatic':patient_symptomatic,
                        'lab_notifier_name':lab_notifier_name,
                        'facility_name':facility_name,
                        'lab_request_pathogen':lab_request_pathogen,
                        'raw_data': json_data,
                        'message_type': 'OML^O21^OML_O21',
                        'country':'ZMB',
                        'nmc_diag_name':nmc_diag_name,
                        'lab_filler_phone_number': lab_filler_phone_number,
                        'case_phone_number':case_phone_number_formatted,
                        'case_disease_code':case_disease_code,
                        'case_loinc_code':case_loinc_code,
                        'case_loinc_name':case_loinc_name,
                        'lab_specimen_sent_date':lab_specimen_sent_date,
                        'lab_specimen_collection_date':lab_specimen_collection_date,
                        'case_rapid_test_done':case_rapid_test_done,
                        'case_notifier_name':case_notifier_name,
                        'case_notifier_designation': case_notifier_designation,
                        'case_specimen_name':case_specimen_name,
                    }
                )
                if created:
                    print(f"{tracked_entity_id} record created in DB")
                    get_event_data.delay(tracked_entity_id)  # Call asynchronously
                    get_hmis_code.delay(event_org_unit_id, tracked_entity_id)  # Call asynchronously
                    return JsonResponse({'status': 'success', 'message': 'Event created'}, status=201)
                else:
                    print(f"{tracked_entity_id} record updated in DB")                                
                    get_event_data.delay(tracked_entity_id)  # Call asynchronously
                    # Check if the hmis_code is null
                    event = WebhookEvent.objects.get(tracked_entity_id=tracked_entity_id)
                    if event.hmis_code is None:
                        print(f"hmis_code is null for {tracked_entity_id}, calling get_hmis_code task")
                        get_hmis_code.delay(event_org_unit_id, tracked_entity_id)  # Call asynchronously                
                    return JsonResponse({'status': 'success', 'message': 'Event updated'}, status=200)
            
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            return JsonResponse({'status': 'success', 'message': 'No LAB CODE'}, status=500)


