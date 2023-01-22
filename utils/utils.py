from flask import Response
import json
import logging
from flask import g, request
import uuid
import os
from config import Config
import re
import pytz
import datetime
import time
import base64
from services import settings_service

LOG_LEVEL = Config.LOG_LEVEL
logging.basicConfig(level=LOG_LEVEL)

def format_response(
    error, message, return_code, data={}, cookies: list = [], headers: list = []
):
    send_data = {"message": message, "error": error, "data": data}
    if error != "":
        send_data["error"] += f", request_id [{g.request_id}]"

    response = Response()
    response.set_data(json.dumps(send_data,indent=4, sort_keys=True, default=str))
    response.status = return_code
    response.content_type = "application/json"
    response.headers["request_id"] = g.request_id

    if len(cookies) > 0:
        for cookie in cookies:
            response.set_cookie(cookie["key"], cookie["value"])

    if len(headers) > 0:
        for header in headers:
            response.headers[header["key"]] = header["value"]

    return response


def log_with_request_id(level, message):
    if level == "i":
        logging.info(f"{g.request_id} - {message}")
    elif level == "d":
        logging.debug(f"{g.request_id} - {message}")
    elif level == "w":
        logging.warn(f"{g.request_id} - {message}")
    elif level == "e":
        logging.error(f"{g.request_id} - {message}")        
    elif level == "f":
        logging.fatal(f"{g.request_id} - {message}")


def add_uuid_to_g():
    g.request_id = uuid.uuid4()

def fetch_settings_if_required_and_add_to_config():
    miliseconds = int (time.time() * 1000)
    if  miliseconds > Config.NEXT_SETTINGS_FETCH:
        log_with_request_id("d","Fetching Settings for fresh data")
        settings = settings_service.get_settings()
        Config.settings = settings
        Config.NEXT_SETTINGS_FETCH = miliseconds + 60000

def validate_access_to_api(path, method,human_user=True):
    if len(Config.validation_config.keys()) == 0:
        with open("utils/validation_config.json") as validation_config_file:
            Config.validation_config = json.load(validation_config_file)

    vc = Config.validation_config    

    fetch_settings_if_required_and_add_to_config()

    if not human_user:
        log_with_request_id("d", f"Handling API request, value of header SD-API-KEY = {request.headers.get('SD-API-KEY')}")        
        # log_with_request_id("d", f"All headers = {request.headers}")        
        settings = Config.settings
        api_key = settings["inbound_api_key"]
        sent_api_key = request.headers.get('SD-API-KEY')

        if api_key == None or sent_api_key == None or sent_api_key != api_key:
            return False, "ACCESS_DENIED"
        else:
            g.user_role = "admin"

    allowed_roles = None
    
    if vc.get(path) != None and vc.get(path).get(method) != None:
        allowed_roles = vc.get(path).get(method).get("role")
    
    if allowed_roles == None:
        return True, "OK"
    else:
        if g.user_role not in allowed_roles:
            return False, "ACCESS_DENIED"

    return True, "OK"


def validate_input(path, method):
    if len(Config.validation_config.keys()) == 0:
        with open("utils/validation_config.json") as validation_config_file:
            Config.validation_config = json.load(validation_config_file)

    vc = Config.validation_config

    if vc.get(path) != None:
        if vc.get(path).get(method) != None:
            log_with_request_id("d", vc.get(path).get(method))
            input = {}
            compare_with = {}
            field_configurations = vc.get(path).get("field_configurations")

            if method == "GET" or method == "DELETE":
                input = request.args
                compare_with = vc.get(path).get(method).get("args")
            else:
                input = request.json if request.json != None else request.form
                compare_with = vc.get(path).get(method).get("body")



            log_with_request_id(
                "d", f"starting mandatory validations for {path}, {method}"
            )
            validation_response = validate_mandatory(
                field_configurations, input, compare_with
            )
            log_with_request_id(
                "d",
                f"done mandatory validations for {path}, {method}, {validation_response}",
            )
            if not validation_response[0]:
                return validation_response

            log_with_request_id(
                "d", f"starting minmax validations for {path}, {method}"
            )
            validation_response = validate_min_maxlength(
                field_configurations, input, compare_with
            )
            log_with_request_id(
                "d",
                f"done minmax validations for {path}, {method}, {validation_response}",
            )
            if not validation_response[0]:
                return validation_response

            log_with_request_id(
                "d", f"starting datatype validations for {path}, {method}"
            )
            validation_response = validate_datatype(
                field_configurations, input, compare_with
            )
            log_with_request_id(
                "d",
                f"done datatype validations for {path}, {method}, {validation_response}",
            )
            if not validation_response[0]:
                return validation_response

    return True, ""


def validate_mandatory(
    field_configurations: dict, input: dict, compare_with_config: dict
) -> tuple:
    if compare_with_config.get("mandatory") == None:
        return True, ""
    error_message = ""
    field_missing = False
    for field in compare_with_config.get("mandatory"):
        if input.get(field) == None or input.get(field) == "":
            error_message += f"{field_configurations.get(field)[0]} is mandatory. "
            field_missing = True

    if field_missing:
        return False, error_message
    else:
        return True, ""


def validate_min_maxlength(
    field_configurations: dict, input: dict, compare_with_config: dict
) -> tuple:
    error_message = ""
    error_found = False
    for field in input.keys():
        if field_configurations.get(field) == None:
            log_with_request_id("d", f"skipping {field}")
            continue
        
        if input.get(field) == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:    
            continue

        log_with_request_id(
            "d",
            f"Checking for {field} type {field_configurations.get(field)[1]} incoming value {input.get(field)}"
        )

        if field_configurations.get(field) == None:
            return False, f"unknown field {field}"

        if compare_with_config.get("skip") != None and field in set(
            compare_with_config.get("skip")
        ):
            log_with_request_id("d", f"skipping {field}")
            continue

        if field_configurations.get(field)[1] == "enum" or field_configurations.get(field)[1] == "range":
            log_with_request_id("d", f"skipping {field}")
            continue        

        value_to_check = input.get(field)
        if field_configurations.get(field)[1] != "string":
            value_to_check = str(input.get(field))

        if (
            len(value_to_check) < field_configurations.get(field)[2]
            or len(value_to_check) > field_configurations.get(field)[3]
        ):
            error_message += f"Length of {field_configurations.get(field)[0]} \
                                    should be between \
                                    {field_configurations.get(field)[2]} \
                                        and {field_configurations.get(field)[3]}. "
            error_found = True

    if error_found:
        return False, error_message
    else:
        return True, ""


def validate_datatype(
    field_configurations: dict, input: dict, compare_with_config: dict
) -> tuple:
    error_message = ""
    error_found = False

    if len(compare_with_config.keys()) == 0:
        return True, error_message

    for field in input.keys():
        if field_configurations.get(field) == None:
            log_with_request_id("d", f"skipping {field}")
            continue

        
        if field_configurations.get(field)[1] == "email":
            if not valid_email(input.get(field)):
                error_message += f"Invalid {field_configurations.get(field)[0]}. "
                error_found = True

        if field_configurations.get(field)[1] == "emails":
            try:
                emails = input.get(field).split(",")
            except BaseException as e:
                error_message += f"Invalid {field_configurations.get(field)[0]}. "
                error_found = True

            for email in emails:
                if not valid_email(email):
                    error_message += f"Invalid {field_configurations.get(field)[0]} - {email} "
                    error_found = True
                    break

        if field_configurations.get(field)[1] == "enum":
            if input.get(field) == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:
                continue            
            if input.get(field) not in field_configurations.get(field)[2]:
                error_message += f"Invalid {field_configurations.get(field)[0]} should be one of {field_configurations.get(field)[2]}. "
                error_found = True

        if field_configurations.get(field)[1] == "number":
            if not valid_amount(input.get(field)):
                error_message += f"Invalid {field_configurations.get(field)[0]}. "
                error_found = True

        if field_configurations.get(field)[1] == "password":
            if not valid_password_string(input.get(field)):
                error_message += f"Invalid {field_configurations.get(field)[0]} \
                                    string, minimum 8 characters, alphanumeric with special characters. "
                error_found = True

        if field_configurations.get(field)[1] == "amount":
            if not valid_amount(input.get(field)):
                error_message += f"Invalid {field_configurations.get(field)[0]}. "
                error_found = True

        if field_configurations.get(field)[1] == "range":
            if not validate_range(input.get(field),field_configurations.get(field)[2]):
                error_message += f"Invalid {field_configurations.get(field)[0]} should be within these limits {field_configurations.get(field)[2]}. "
                error_found = True                

        if field_configurations.get(field)[1] == "file_name":
            if not input.get(field).endswith(".pdf"):
                error_message += f"Invalid {field_configurations.get(field)[0]}, only .pdf files are allowed. "
                error_found = True

        if field_configurations.get(field)[1] == "custom":
            if not validate_custom(field, input.get(field)):
                error_message += f"Invalid {field_configurations.get(field)[0]}. "
                error_found = True

    if error_found:
        return False, error_message
    else:
        return True, ""



def valid_email(email:str):
    # don't test blank strings for datatype
    email = email.strip()
    if email == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:    
        return True
    else:        
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if re.fullmatch(regex, email):
            return True
        return False


def valid_password_string(password: str):
    special_char = ["$", "@", "#", "%"]
    is_valid = True
    if not any(char.isdigit() for char in password):
        is_valid = False
    if not any(char.isupper() for char in password):
        is_valid = False
    if not any(char.islower() for char in password):
        is_valid = False
    if not any(char in special_char for char in password):
        is_valid = False

    return is_valid


def valid_amount(amount: str):
    if amount == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:    
        return True    
    try:
        float(amount)
    except:
        return False
    return True

def validate_custom(field_type:str, field_value):
    if field_value == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:    
        return True  
    if field_type  == "key_resource_name":
        try:
            key_resource_arr = field_value.split("/")
            if len(key_resource_arr) == 8:
                return True
            else:
                return False    
        except:
            return False

def validate_range(value:int,bounds:list):
    if value == "" and Config.validation_config["common_settings"]["consider_blank_as_none"]:    
        return True  
    try:
        if value >= bounds[0] and value <= bounds[1]:
            return True
        else:
            return False    
    except:
        return False

def get_date_time(offset):
    now = datetime.datetime.now(pytz.timezone(Config.PYTZ_TIME_ZONE))
    if isinstance(offset,str):
        offset = int(offset)
    if offset > 0:
        then = now + datetime.timedelta(days=offset)
        return datetime.datetime.fromtimestamp(then.timestamp(),pytz.timezone(Config.PYTZ_TIME_ZONE))
    else:
        return now

def get_date_in_configured_tz(date_from_db):
    try:
        return datetime.datetime.fromtimestamp(date_from_db.timestamp(),pytz.timezone(Config.PYTZ_TIME_ZONE))
    except:
        return ""    


def get_message_to_encrypt():
    message = "Hello World"
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message       

def set_current_user_role(request):
    user_email = request.headers.get('X-Goog-Authenticated-User-Email')

    g.user_email = None
    g.user_role = None       
    fetch_settings_if_required_and_add_to_config()
 
    if user_email == None:
        if os.environ.get("SETUP_RUN") == "Y":
               g.user_email = os.environ.get("SETUP_USER_EMAIL")
               g.user_role = os.environ.get("SETUP_ROLE")
               return
    else:
        g.user_email = user_email.replace("accounts.google.com:","")
        g.user_role = "non_admin"
        if g.user_email in Config.settings["admin_emails"]:
            g.user_role = "admin"
