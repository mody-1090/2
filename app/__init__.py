# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

# تحميل متغيرات البيئة
load_dotenv()

# إنشاء التطبيق
app = Flask(__name__)

# تحميل الإعدادات من config.py
app.config.from_object('app.config.Config')

# تهيئة الإضافات
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth_routes.login"  # تحديد مسار تسجيل الدخول
login_manager.login_message_category = "info"

# استيراد النماذج بعد تهيئة `db`
from app.models import User

# ✅ تعريف `user_loader` هنا
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





# استيراد النماذج (لتجنب مشاكل الاستيراد الدائري)
from app import models

# تسجيل Blueprints (المسارات)
from app.routes.main_routes import main_routes
from app.routes.api_routes import api_routes
from app.routes.auth_routes import auth_routes

app.register_blueprint(main_routes)
app.register_blueprint(api_routes, url_prefix="/api")
app.register_blueprint(auth_routes, url_prefix="/auth")
