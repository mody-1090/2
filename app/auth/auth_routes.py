from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app.models import db, User
import uuid
from app.forms import RegistrationForm
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
        
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, email=email, password=hashed_password, phone=phone, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        flash("✅ تم إنشاء الحساب بنجاح!", "success")
        return redirect(url_for("auth_routes.login"))
    
    return render_template("register.html", form=form)




@auth_routes.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            reset_token = str(uuid.uuid4())  # إنشاء رمز فريد
            user.reset_token = reset_token
            db.session.commit()
            flash("✅ تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.", "success")
        else:
            flash("❌ البريد الإلكتروني غير مسجل.", "danger")
    
    return render_template("forgot_password.html")
