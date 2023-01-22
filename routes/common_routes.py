from utils import utils
import traceback
from flask import Blueprint, request
from services import common_service
from flask import g
from config import Config
import os

blueprint = Blueprint("common_routes", __name__)


@blueprint.route("/app_info", methods=["GET"])
def get_app_info():
    try:
        utils.log_with_request_id(
            "d",
            f"start - Getting application information"
        )

        version = common_service.get_application_version()

        # could be up to 5 minutes late
        application_name = Config.settings["application_name"]
        
        utils.log_with_request_id(
            "d",
            f"done -  Getting application information"
        )
        # we always return arrays so [output]
        return utils.format_response(
            "", "", 200, {"version": version,
                          "application_name": application_name,"setup_run":os.environ.get("SETUP_RUN", "N")}
        )
    except BaseException as e:
        description = "error - Getting application version"
        utils.log_with_request_id(
            "e",
            description
        )
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)


@blueprint.route("/user_info", methods=["GET"])
def get_user_info():
    try:
        utils.log_with_request_id(
            "d",
            f"start - Getting User Info"
        )

        user_email = g.user_email
        user_role = g.user_role
        output = {"user_email": user_email, "user_role": user_role}

        if user_email == None or user_role == None:
            return utils.format_response(
                "No Login Information", "", 401, None
            )
        utils.log_with_request_id(
            "d",
            f"done -  Getting User Info"
        )
        return utils.format_response(
            "", "", 200, output
        )
    except BaseException as e:
        description = "error - Getting User Info"
        utils.log_with_request_id(
            "e",
            description
        )
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)
