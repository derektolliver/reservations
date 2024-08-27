from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY_IN_SECONDS = 86400

def validate_timestamp(timestamp):
    try:
        datetime.strptime(timestamp, DATETIME_FORMAT)
        return True
    except ValueError:
        return False
    
def format_timestamp(timestamp):
    return datetime.strptime(timestamp, DATETIME_FORMAT)