from app import db
from app.models import Notification

def create_notification(user_id, message):
    """إنشاء إشعار جديد للمستخدم"""
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()
