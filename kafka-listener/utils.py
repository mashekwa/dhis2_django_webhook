import re
import pandas as pd
import os
import hl7
import logging
from requests import Session
import requests

# Helper functions for API calls
def get_data(endpoint, conn_id):
    try:
        session = Session()
        response = session.get(f"http://{conn_id}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.exception(f"Failed to retrieve data from API: {e}")
        raise

def post_data_api(endpoint, payload, headers, conn_id):
    try:
        session = Session()
        response = session.post(f"http://{conn_id}{endpoint}", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.exception(f"Failed to post data to API: {e}")
        raise

def normalize_to_short_date(date_str):
    return re.sub(r'^(\d{4})(\d{2})(\d{2})(\d{2}\d{2})$', r'\1-\2-\3', date_str)

def util_lists_to_dict(keys, values):
    return dict(zip(keys, values))

def map_laboratory_result(lab_result):
    mapping_file = 'mappings/disa_labresults_dhis_mapping.csv'
    df = pd.read_csv(os.path.join('./app', mapping_file))
    lab_result_cleaned = re.sub(r"\s+", "_", lab_result).strip().lower()
    df["disa_result"] = df["disa_result"].str.replace(r"\s+", "_", regex=True).str.strip().str.lower()
    result_row = df[df["disa_result"] == lab_result_cleaned]
    return result_row['dhis_code'].iloc[0] if not result_row.empty else "ERROR"


