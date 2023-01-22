from utils import utils
import traceback
from flask import Blueprint, request
from services import settings_service

blueprint = Blueprint("settings_routes", __name__)

@blueprint.route("/settings",methods=["GET"])
def get_settings():
    try:    
        
        utils.log_with_request_id(
        "d",
        f"start - retrieving all settings"
        )
        settings = settings_service.get_settings()
        utils.log_with_request_id(
        "d",
        f"done - retrieving all settings"
        )

        return utils.format_response(
            "", "", 200, settings
        )        
    except BaseException as e:
        description = "error - retrieving settings"
        utils.log_with_request_id(
            "e",
            description
        )
        # prints trace
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}","",500)


@blueprint.route("/settings", methods=["POST","PUT"])
def update_settings():
    try:    
        utils.log_with_request_id(
        "w",
        "start - updating settings"
        )    
        
        settings_service.update_settings(request.json)
        
        utils.log_with_request_id(
        "w",
        "done - updating settings"
        )   
        return utils.format_response("",
                                    f"Updated Settings Successfully",  200, ""
                                    )
    except BaseException as e:
        description = "error - updating settings"
        utils.log_with_request_id(
            "e",
            description
        )
        # prints trace
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}","",500)
