import os


class Config:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING").upper()
    PYTZ_TIME_ZONE = os.environ.get("PYTZ_TIME_ZONE", "Asia/Kolkata")
    API_RUN = os.environ.get("API_RUN", "N")
    validation_config = {}
    NEXT_SETTINGS_FETCH=0
    settings = {}
