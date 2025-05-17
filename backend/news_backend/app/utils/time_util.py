from datetime import datetime, timedelta

def china_time_now():
    return datetime.utcnow() + timedelta(hours=8) 