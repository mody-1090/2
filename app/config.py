import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

class Config:
    """إعدادات التطبيق"""
    
    # مفتاح التشفير
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
    
    # إعدادات قاعدة البيانات
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # اتصال قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # إعدادات Redis (إذا كنت تستخدم Celery)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
