from database.db import db_client
import datetime, pytz
from config import Config
from utils import utils


def update_cache_document(update_dict: dict):
    if not db_client.collection("kms_prober_data").document("cache").get().exists:
        get_cache_document()
    db_client.collection("kms_prober_data").document(
            "cache").update(update_dict)



def get_cache_document():
    doc = db_client.collection("kms_prober_data").document("cache").get()
    if doc.exists:
        doc_dict = doc.to_dict()
        doc_dict["latest_job_end_time"] = utils.get_date_in_configured_tz(date_from_db=doc_dict["latest_job_end_time"])
        return doc_dict
    else:
        initialized_cache = {"total_number_of_keys": 0,
                             "keys_failed_in_latest_job": 0, "latest_job_end_time": "", "avg_key_response_time": 0}
        db_client.collection("kms_prober_data").document(
            "cache").set(initialized_cache)
        return initialized_cache
