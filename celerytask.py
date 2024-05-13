
from celery import Celery
import redis
import json
from celery.schedules import crontab
import requests

app = Celery('send_reminder', broker='redis://localhost:6379/0')

r = redis.Redis(host='localhost', port=6379, db=0)

WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAAPhiyV0Q/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=qChrK97fN2748VDsFJFeRbbrmV6RmtR2FZwXDQuwp_M%3D"

@app.task
def send_message():
    message = {
        "text": "This message is from REDIS and CELERY! Please visit http://localhost:8080/feed",
    }
    response = requests.post(WEBHOOK_URL, json=message)

    if not response.ok:
        raise Exception(f"Failed to send message: {response.status_code}")
    else:
        return "Reminder message sent successfully."

# Schedule the task to run every minute
app.conf.beat_schedule = {
    "send-reminder": {
        "task": "send_reminder.send_message",
        "schedule": crontab(minute="*"),
    }
}
