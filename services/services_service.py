from database.db import db_client
from entity.Service import Service
from utils import utils
import datetime
import base64
import traceback
import time
from services import cache_service, settings_service
from google.cloud import firestore
import pytz
from config import Config
from services import mail_service
from flask import g


def format_document_id(service_name: str):
    document_id = service_name.lower().strip().replace(" ", "_")
    return document_id


def add_a_service(service_name: str, description: str, notification_recipients: str):
    utils.log_with_request_id(
        "d",
        f"start - Adding Service {service_name}"
    )
    curr_time = utils.get_date_time(0)
    settings = settings_service.get_settings()
    new_service = Service(service_name=service_name, description=description, notification_recipients=notification_recipients,
                          status="active", message="Service operating normally", status_time=curr_time)
    db_client.collection("service_dashboard_data").document("services").collection("all_services").document(
        format_document_id(service_name)).set(new_service.to_dict())
    add_service_histroy(settings,service_name,curr_time,"active","Service operating normally")
    cache_service.update_cache_document(
        {"total_number_of_services": firestore.Increment(1)})
    utils.log_with_request_id(
        "d",
        f"done - Adding Service {service_name}"
    )

    return new_service.service_name

def add_service_based_on_role(array_to_return:list,current_service_doc:dict):
    if g.user_role != "admin":
        current_service_doc["notification_recipients"] = ""
    array_to_return.append(current_service_doc)    


def search_services(service_name: str, page_number: int):

    last_doc = None
    last_service_name_with_status = None
    list_of_services_to_return = []

    query = db_client.collection("service_dashboard_data").document(
        "services").collection("all_services")

    if service_name != None:
        utils.log_with_request_id(
            "d",
            f"Searching for Service {service_name}")        
        doc = query.document(format_document_id(service_name)).get()
        docs = []
        if doc.exists:
            docs = [doc]
            for doc in docs:
                curr_doc = doc.to_dict()
                add_service_based_on_role(list_of_services_to_return,curr_doc)
    if service_name == None:
        if page_number == 1:
            docs = query.order_by("status_with_name", direction=firestore.Query.DESCENDING).limit(5).stream()
            for doc in docs:
                curr_doc = doc.to_dict()
                add_service_based_on_role(list_of_services_to_return,curr_doc)
        else:
            last_service_name_with_status = None
            docs = query.order_by("status_with_name", direction=firestore.Query.DESCENDING).limit(
                5*(page_number-1)).stream()
            last_doc = list(docs)[-1]
            last_doc_dict = last_doc.to_dict()
            last_service_name_with_status = last_doc_dict["status_with_name"]
            utils.log_with_request_id(
                "d",
                f"start - Fetching from service {last_service_name_with_status}"
            )
            docs = query.order_by("status_with_name", direction=firestore.Query.DESCENDING).start_after(
                {"status_with_name": last_service_name_with_status}).limit(5).stream()

            for doc in docs:
                curr_doc = doc.to_dict()
                add_service_based_on_role(list_of_services_to_return,curr_doc)
            utils.log_with_request_id(
                "d",
                f"done - Fetching from service {last_service_name_with_status}"
            )

    return list_of_services_to_return


def delete_a_service(service_name: str):
    db_client.collection("service_dashboard_data").document(
        "services").collection("all_services").document(format_document_id(service_name)).delete()

    cache_service.update_cache_document(
        {"total_number_of_services": firestore.Increment(-1)})


def update_a_service(updated_service: dict):
    settings = settings_service.get_settings()
    service_name = updated_service["service_name"]
    utils.log_with_request_id(
        "d",
        f"start - Updating service {service_name}"
    )
    doc_ref = db_client.collection("service_dashboard_data").document(
        "services").collection("all_services").document(format_document_id(service_name))
    doc = doc_ref.get()
    curr_time = utils.get_date_time(0)


    if doc.exists:
        doc_dict = doc.to_dict()  # gcp to dict - still gives proper dict

        if doc_dict["status"] != updated_service["status"]:
            utils.log_with_request_id(
                "d",
                f"Updating service history {service_name}"
            )
            add_service_histroy(settings,service_name,curr_time,updated_service["status"],updated_service["message"])
            add_to_messages(settings,service_name,curr_time,doc_dict["status"],updated_service["status"],updated_service["message"])
            mail_service.send_alert_email(settings,service_name,curr_time,doc_dict["status"],updated_service["status"], updated_service["message"],doc_dict["notification_recipients"])

        updated_service["status_with_name"] = f'{updated_service["status"]}_{service_name}'
        db_client.collection("service_dashboard_data").document("services").collection("all_services").document(
        format_document_id(service_name)).set(updated_service)        
        
        utils.log_with_request_id(
        "d",
        f"done - Updating service {service_name}"
        )

    else:
        utils.log_with_request_id(
        "d",
        f"Did not find service {service_name}"
        )         


def add_service_histroy(settings,service_name,curr_time,status,message):
    ttl_value = utils.get_date_time(settings["data_retention_days"])
    miliseconds = int(time.time() * 1000)
    db_client.collection("service_dashboard_data").document(
    "services").collection("all_history").document(format_document_id(service_name)).collection("history").add({ # random document id
        "timestamp":miliseconds,"from_time": curr_time, "status": status, "message": message, "ttl":ttl_value
    })            


def add_to_messages(settings,service_name,curr_time,prev_status,new_status,message):
    ttl_value = utils.get_date_time(settings["data_retention_days"])
    db_client.collection("service_dashboard_data").document(
    "services").collection("all_messages").add({ # random document id
        "service_name":service_name,"from_time": curr_time, "prev_status": prev_status,"new_status": new_status,  "message": message, "ttl":ttl_value
    })   

def get_service_history(service_name:str,page_number:int):

    last_doc = None
    last_time_stamp = None
    history_records_to_return = []

    query = db_client.collection("service_dashboard_data").document(
    "services").collection("all_history").document(format_document_id(service_name)).collection("history")


    if page_number == 1:
        docs = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()
        for doc in docs:
            curr_doc_dict = doc.to_dict()
            curr_doc_dict["from_time"] = utils.get_date_in_configured_tz(date_from_db=curr_doc_dict["from_time"])            
            history_records_to_return.append(curr_doc_dict)
    else:
        last_time_stamp = None
        docs = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(
            5*(page_number-1)).stream()
        last_doc = list(docs)[-1]
        last_time_stamp = last_doc.to_dict()["timestamp"]

        utils.log_with_request_id(
            "d",
            f"start - Fetching from timestamp {last_time_stamp}"
        )
        # now get from the last one
        docs = query.order_by("timestamp", direction=firestore.Query.DESCENDING).start_after(
            {"timestamp": last_time_stamp}).limit(5).stream()

        for doc in docs:
            curr_doc_dict = doc.to_dict()
            curr_doc_dict["from_time"] = utils.get_date_in_configured_tz(date_from_db=curr_doc_dict["from_time"])
            history_records_to_return.append(curr_doc_dict)
        utils.log_with_request_id(
            "d",
            f"done - Fetching from timestamp {last_time_stamp}"
        )
    return history_records_to_return


def get_recent_messages():
    utils.log_with_request_id(
        "d",
        f"start - Fetching recent 10 messages"
    )    
    query = db_client.collection("service_dashboard_data").document(
    "services").collection("all_messages")
    message_records_to_return = []
    docs = query.order_by("from_time", direction=firestore.Query.DESCENDING).limit(10).stream()
    for doc in docs:
        curr_doc_dict = doc.to_dict()
        curr_doc_dict["from_time"] = utils.get_date_in_configured_tz(date_from_db=curr_doc_dict["from_time"])
        message_records_to_return.append(curr_doc_dict)    

    utils.log_with_request_id(
    "d",
    f"done - Fetching recent 10 messages"
    )     
    return message_records_to_return