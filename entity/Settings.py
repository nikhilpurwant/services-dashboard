class Settings(object):
    def __init__(self, application_name, application_url, data_retention_days,  sendgrid_api_key, admin_emails,alert_from_email,inbound_api_key):
        self.application_url = application_url
        self.data_retention_days = data_retention_days
        self.sendgrid_api_key = sendgrid_api_key
        self.admin_emails = admin_emails
        self.application_name = application_name
        self.alert_from_email = alert_from_email
        self.inbound_api_key = inbound_api_key


    def to_dict(self):
        output = {
            "application_url": self.application_url,
            "application_name": self.application_name,
            "admin_emails": self.admin_emails,
            "data_retention_days": self.data_retention_days,
            "sendgrid_api_key": self.sendgrid_api_key,
            "alert_from_email": self.alert_from_email,
            "inbound_api_key": self.inbound_api_key
        }
        return output
