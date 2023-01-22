from utils import utils
import traceback
from flask import Blueprint, request
from services import services_service

blueprint = Blueprint("services_routes", __name__)


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


@blueprint.route("/services", methods=["POST"])
def add_a_service():
    try:    
        service_name = services_service.add_a_service(request.json.get("service_name"),
                                        request.json.get("description"), request.json.get("notification_recipients"))

        return utils.format_response("",
                                    f"service Added - {service_name}",  200, ""
                                    )
    except BaseException as e:
        description = "error - adding service"
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



@blueprint.route("/services", methods=["DELETE"])
def delete_a_service():
    try:    
        service_name = request.json.get("service_name")
        services_service.delete_a_service(service_name)
        return utils.format_response("",
                                    f"service Deleted - {service_name}",  200, ""
                                    )
    except BaseException as e:
        description = "error - deleting service"
        utils.log_with_request_id(
            "e",
            description
        )
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)




@blueprint.route("/services/history", methods=["GET"])
def get_service_history():
    try:

        utils.log_with_request_id(
            "d",
            f"start - retrieving service history with parameters {request.args}"
        )
        service_name = request.args.get("service_name")
        page_number = request.args.get("page_number")
        
        if page_number == None:
            page_number=1
        else:
            page_number = int(page_number)

        data = services_service.get_service_history(service_name,page_number)

        utils.log_with_request_id(
            "d",
            f"done - retrieving service history with parameters {request.args}"
        )

        return utils.format_response("",
                                     f"service search - ok",  200, data
                                     )

    except BaseException as e:
        description = "error - retrieving service history"
        utils.log_with_request_id(
            "e",
            description
        )
        # prints trace
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)


@blueprint.route("/services/messages", methods=["GET"])
def get_latest_messages():
    try:

        utils.log_with_request_id(
            "d",
            f"start - retrieving latest messages with parameters {request.args}"
        )
        service_name = request.args.get("service_name")
        page_number = request.args.get("page_number")
        
        if page_number == None:
            page_number=1
        else:
            page_number = int(page_number)

        data = services_service.get_recent_messages()

        utils.log_with_request_id(
            "d",
            f"done - retrieving latest messages with parameters {request.args}"
        )

        return utils.format_response("",
                                     f"latest messages search - ok",  200, data
                                     )

    except BaseException as e:
        description = "error - retrieving latest messages"
        utils.log_with_request_id(
            "e",
            description
        )
        # prints trace
        traceback.print_exc()
        return utils.format_response(f"{description} - internal error - {e}", "", 500)
