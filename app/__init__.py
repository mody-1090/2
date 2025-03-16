import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_mail import Mail

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

# ✅ تهيئة Flask-Mail لاستخدام Brevo SMTP
app.config["MAIL_SERVER"] = "smtp-relay.brevo.com"  # خادم SMTP من Brevo
app.config["MAIL_PORT"] = 587  # المنفذ
app.config["MAIL_USE_TLS"] = True  # يجب تفعيل TLS
app.config["MAIL_USE_SSL"] = False


# ✅ حسابات البريد المخصصة لكل نوع من العمليات
app.config["MAIL_NO_REPLY"] = os.getenv("MAIL_NO_REPLY", "no-reply@yourdomain.com")  # البريد المستخدم في التسجيل
app.config["MAIL_SUPPORT"] = os.getenv("MAIL_SUPPORT", "support@yourdomain.com")  # البريد المستخدم في الدعم الفني
app.config["MAIL_INFO"] = os.getenv("MAIL_INFO", "info@yourdomain.com")  # البريد المستخدم في تواصل معنا

# ✅ بيانات تسجيل الدخول لـ Brevo SMTP
app.config["MAIL_USERNAME"] = os.getenv("BREVO_SMTP_USERNAME")  # اسم المستخدم (يتم تحميله من .env)
app.config["MAIL_PASSWORD"] = os.getenv("BREVO_SMTP_PASSWORD")  # كلمة المرور (يتم تحميلها من .env)

mail = Mail(app)  # تهيئة Flask-Mail

# ✅ ربط الإضافات بالتطبيق
db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
login_manager.init_app(app)
mail.init_app(app)  # ربط Brevo SMTP

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
