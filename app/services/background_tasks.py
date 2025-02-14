# app/services/background_tasks.py
from celery import Celery
from app.config import Config

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

@celery.task
def send_email_task(to_email, subject, message):
    # مثال لإرسال بريد إلكتروني في الخلفية
    print(f"Sending email to {to_email} with subject '{subject}'")
    # يمكنك دمج مكتبة مثل smtplib أو flask-mail هنا.
