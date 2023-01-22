class Cache(object):
    def __init__(self, total_number_of_keys, latest_job_end_time, keys_failed_in_latest_job, avg_key_response_time):
        self.total_number_of_keys = total_number_of_keys
        self.latest_job_end_time = latest_job_end_time
        self.keys_failed_in_latest_job = keys_failed_in_latest_job
        self.avg_key_response_time = avg_key_response_time

    def to_dict(self):
        output = {
            "total_number_of_keys": self.total_number_of_keys,
            "alert_type": self.alert_type,
            "latest_job_end_time": self.latest_job_end_time,
            "keys_failed_in_latest_job": self.keys_failed_latest_job,
            "avg_key_response_time": self.avg_key_response_time
        }
        return output
