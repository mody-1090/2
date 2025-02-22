# app/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

# ✅ تحميل متغيرات البيئة مبكرًا
load_dotenv()

# ✅ إنشاء التطبيق
app = Flask(__name__)

# ✅ تحميل الإعدادات من config.py
app.config.from_object('app.config.Config')

# ✅ تهيئة الإضافات
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth_routes.login"  # تحديد مسار تسجيل الدخول
login_manager.login_message_category = "info"

# ✅ ربط الإضافات بالتطبيق
db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
login_manager.init_app(app)

# ✅ تعريف `user_loader`
from app.models import User  # استيراد النموذج لتسجيل المستخدم
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ تسجيل Blueprints (المسارات)
from app.routes.main_routes import main_routes
from app.routes.api_routes import api_routes
from app.routes.auth_routes import auth_routes

app.register_blueprint(main_routes)
app.register_blueprint(api_routes, url_prefix="/api")
app.register_blueprint(auth_routes, url_prefix="/auth")
