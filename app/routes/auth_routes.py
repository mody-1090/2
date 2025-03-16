from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app.models import db, User
import uuid
from app.forms import RegistrationForm
from flask_mail import Message
from app import mail, app  # تأكد من تهيئة Flask-Mail في `app/__init__.py`

# إنشاء Blueprint لمسارات المصادقة
auth_routes = Blueprint("auth_routes", __name__)

@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("✅ تم تسجيل الدخول بنجاح!", "success")
            return redirect(url_for("main_routes.dashboard"))
        else:
            flash("❌ بيانات تسجيل الدخول غير صحيحة.", "danger")
    
    return render_template("login.html")

@auth_routes.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("✅ تم تسجيل الخروج بنجاح!", "success")
    return redirect(url_for("auth_routes.login"))

@auth_routes.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        phone = form.phone.data
        role = form.role.data  # سيكون "intermediary" من الحقل المخفي

        if role not in ["admin", "intermediary"]:
            flash("⚠️ دور المستخدم غير صالح!", "danger")
            return redirect(url_for("auth_routes.register"))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("❌ البريد الإلكتروني مسجل مسبقًا.", "danger")
            return redirect(url_for("auth_routes.register"))
        
        # تشفير كلمة المرور
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, email=email, password=hashed_password, phone=phone, role=role)
        
        db.session.add(new_user)
        db.session.commit()

        # تسجيل دخول المستخدم فورًا
        session["user_id"] = new_user.id

        # إرسال بريد إلكتروني يحتوي على بيانات الدخول
        send_welcome_email(email, username, password)

        flash("✅ تم إنشاء الحساب وتسجيل الدخول بنجاح!", "success")
        return redirect(url_for("main_routes.dashboard"))
    
    return render_template("register.html", form=form)

def send_welcome_email(recipient, username, raw_password):
    """إرسال بريد الترحيب بعد تسجيل المستخدم الجديد"""
    msg = Message(
        subject="🎉 مرحباً بك في منصتنا - تفاصيل الدخول",
        sender=app.config["MAIL_NO_REPLY"],  # ✅ استخدام بريد no-reply
        recipients=[recipient],
        body=f"""
مرحباً {username},

تم إنشاء حسابك بنجاح!
تفاصيل الدخول الخاصة بك:
📧 البريد الإلكتروني: {recipient}
🔑 كلمة المرور: {raw_password}

🔹 يمكنك تغيير كلمة المرور لاحقًا من خلال صفحة الإعدادات أو استخدام خيار "استعادة كلمة المرور".

شكراً لانضمامك إلينا!
jumlat.com
"""
    )
    mail.send(msg)


def send_reset_email(to_email, reset_url):
    """إرسال بريد إلكتروني يحتوي على رابط إعادة تعيين كلمة المرور"""
    msg = Message(
        subject="🔄 إعادة تعيين كلمة المرور",
        sender=app.config["MAIL_NO_REPLY"],  # ✅ استخدام بريد no-reply
        recipients=[to_email],
        body=f"""
مرحبًا،

لقد طلبت إعادة تعيين كلمة المرور الخاصة بك.
يرجى النقر على الرابط التالي لإدخال كلمة مرور جديدة:

🔗 {reset_url}

إذا لم تطلب ذلك، يمكنك تجاهل هذا البريد.

jumlat.com
"""
    )
    mail.send(msg)

 



@auth_routes.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """طلب إعادة تعيين كلمة المرور"""
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            user.generate_reset_token()  # توليد رمز فريد
            reset_url = url_for("auth_routes.reset_password", token=user.reset_token, _external=True)
            send_reset_email(user.email, reset_url)
            flash("✅ تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.", "success")
        else:
            flash("❌ البريد الإلكتروني غير مسجل.", "danger")

    return render_template("forgot_password.html")

@auth_routes.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """إعادة تعيين كلمة المرور باستخدام رمز الاستعادة"""
    user = User.query.filter_by(reset_token=token).first()

    if not user:
        flash("❌ رمز إعادة التعيين غير صالح أو منتهي الصلاحية.", "danger")
        return redirect(url_for("auth_routes.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("❌ كلمتا المرور غير متطابقتين.", "danger")
            return redirect(url_for("auth_routes.reset_password", token=token))

        # تحديث كلمة المرور وإزالة الرمز
        user.password = generate_password_hash(new_password)
        user.clear_reset_token()
        flash("✅ تم تحديث كلمة المرور بنجاح! يمكنك الآن تسجيل الدخول.", "success")
        return redirect(url_for("auth_routes.login"))

    return render_template("reset_password.html", token=token)


