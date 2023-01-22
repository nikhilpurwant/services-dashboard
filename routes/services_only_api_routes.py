from utils import utils
import traceback
from flask import Blueprint, request
from services import services_service

blueprint = Blueprint("services_only_api_routes", __name__)


@blueprint.route("/services", methods=["GET"])
def get_services():
    try:

        utils.log_with_request_id(
            "d",
            f"start - retrieving services with parameters {request.args}"
        )
        service_name = request.args.get("service_name")
        page_number = request.args.get("page_number")
        
        if page_number == None:
            page_number=1
        else:
            page_number = int(page_number)

        data = services_service.search_services(service_name,page_number)

        utils.log_with_request_id(
            "d",
            f"done - retrieving services with parameters {request.args}"
        )

        return utils.format_response("",
                                     f"service search - ok",  200, data
                                     )

    except BaseException as e:
        description = "error - retrieving services"
        utils.log_with_request_id(
            "e",
            description
        )
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)

@blueprint.route("/services", methods=["PUT"])
def update_a_service():
    try:    
        services_service.update_a_service(request.json)
        return utils.format_response("",
                                    f"service Updated - {request.json.get('service_name')}",  200, ""
                                    )
    except BaseException as e:
        description = f"error - updating service {request.json.get('service_name')}"
        utils.log_with_request_id(
            "e",
            description
        )
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)


