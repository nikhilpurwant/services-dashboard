from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from services import settings_service
from utils import utils

def create_message(settings,service_name,curr_time,old_status,new_status,message):
    html_message = f"Service - <b>{service_name}</b><br>New Status -  <b>[{new_status}]</b><br> Old status - <b>{old_status}</b><br> Time - <b>{curr_time}</b><br>Details - <b>{message}</b><br>"
    
    if settings["application_url"] != "":
        app_url = settings["application_url"] 
        html_message = html_message + f"<br> You can visit <a href='{app_url}'>{settings['application_name']}</a> to track the latest status and history."
    else:
        html_message = html_message + f"<br> You can visit {settings['application_name']} to track the latest status and history."
    
    html_message = html_message + f"<br><br> -Regards <br>{settings['application_name']}"
    return html_message

def send_alert_email(settings,service_name,curr_time,old_status,new_status,message,to_emails):
    output = "Email Sent"
    utils.log_with_request_id(
    "i",
    f"start - Sending Alert Email"
    )    
    try:
        sendgrid_api_key = settings["sendgrid_api_key"]
        alert_from_email=settings["alert_from_email"]
        alert_to_emails=to_emails

        if sendgrid_api_key == "" or alert_from_email == "" or alert_to_emails == "":
            output = "Sending Alert Email - missing email configuration. Skipping."
            utils.log_with_request_id(
            "w", # must be printed
            f"warning - {output}"
            )   
            return output

        message = Mail(
            from_email = alert_from_email,
            to_emails = alert_to_emails.split(","),
            subject=f"{settings['application_name']} - Alert",
            html_content=create_message(settings,service_name,curr_time,old_status,new_status,message))

        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        output = f"Sent Alert Email, status_code - {response.status_code}"       
        utils.log_with_request_id(
        "i",
        f"done - {output}"
        )           
        return output
    except Exception as e:
        output = f"Sending Alert Email {e}"    
        utils.log_with_request_id(
        "w",
        f"error - {output}"
        )   
        return output


