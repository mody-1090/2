import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# استرجاع المتغيرات
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")

import boto3

# إنشاء عميل S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    """التحقق من أن الملف له امتداد مسموح."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file_to_s3(file, intermediary_id):
    """رفع ملف إلى S3 داخل مجلد الوسيط المحدد"""
    file_name = file.filename
    folder_name = f"intermediaries/intermediary_{intermediary_id}"  # اسم المجلد داخل S3
    s3_path = f"{folder_name}/{file_name}"  # المسار الكامل داخل S3

    try:
        s3_client.upload_fileobj(file, S3_BUCKET_NAME, s3_path)
        file_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_path}"
        return file_url  # إرجاع رابط الملف
    except Exception as e:
        print(f"❌ خطأ أثناء الرفع إلى S3: {e}")
        return None

def get_intermediary_folder(intermediary_id):
    """إرجاع اسم المجلد الخاص بالوسيط في S3"""
    return f"intermediaries/intermediary_{intermediary_id}"
