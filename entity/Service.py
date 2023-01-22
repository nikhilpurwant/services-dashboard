class Service(object):
    def __init__(self, service_name, description, notification_recipients, message, status,status_time):
        self.service_name = service_name
        self.description = description
        self.notification_recipients = notification_recipients
        self.message = message
        self.status = status
        self.status_time = status_time
        self.status_with_name = f'{status}_{service_name}'


    def to_dict(self):
        output = {
            "service_name": self.service_name,
            "description": self.description,
            "notification_recipients": self.notification_recipients,
            "message": self.message,
            "status": self.status,
            "status_time": self.status_time,
            "status_with_name": self.status_with_name
        }
        return output
