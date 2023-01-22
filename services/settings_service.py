from database.db import db_client
from entity.Settings import Settings
from utils import utils
from config import Config


def update_settings(updated_settings:dict):
    utils.log_with_request_id(
        "d",
        f"start - Updating Settings"
    )

    db_client.collection("service_dashboard_data").document("settings").update(updated_settings)
    utils.log_with_request_id(
        "d",
        f"done - Updating Settings"
    )


def get_settings():
    doc = db_client.collection("service_dashboard_data").document("settings").get()
    if doc.exists:
        doc_dict = doc.to_dict()
    else:
        initialized_settings = Settings("Service Dashboard","","15","","","","")
        db_client.collection("service_dashboard_data").document(
            "settings").set(initialized_settings.to_dict())
        
        doc_dict = initialized_settings.to_dict()

    doc_dict["log_level"] = Config.LOG_LEVEL
    doc_dict["configured_time_zone"] = Config.PYTZ_TIME_ZONE 

    return doc_dict

