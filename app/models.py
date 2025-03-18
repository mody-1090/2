# app/models.py
from app import db
from datetime import datetime
from flask_login import UserMixin
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(15), nullable=False, default="intermediary")  # "admin" أو "intermediary"
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)  # ✅ حقل جديد لحفظ رمز الاستعادة
    def set_password(self, password):
        """تشفير كلمة المرور عند إنشائها"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """التحقق من صحة كلمة المرور"""
        return check_password_hash(self.password, password)

    def generate_reset_token(self):
        """توليد رمز فريد لإعادة تعيين كلمة المرور"""
        self.reset_token = str(uuid.uuid4())  # إنشاء رمز فريد
        db.session.commit()

    def clear_reset_token(self):
        """إزالة رمز الاستعادة بعد الاستخدام"""
        self.reset_token = None
        db.session.commit()

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"



class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # رابط الصورة المخزنة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)









class WithdrawalRequest(db.Model):
    __tablename__ = "withdrawal_requests"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    intermediary_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    bank_name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    iban_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    account_holder = db.Column(db.String(255), nullable=False)
    intermediary = db.relationship("User", backref=db.backref("withdrawals", lazy="dynamic"))

class FactoryAgreement(db.Model):
    __tablename__ = "factory_agreements"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    agreement_link = db.Column(db.String(255), unique=True, nullable=False)
    bank_account = db.Column(db.String(50), nullable=True)
    carton_price = db.Column(db.Float, nullable=False, default=1.5)
    status = db.Column(db.String(20), default="pending")
    signatory_name = db.Column(db.String(255), nullable=True)
    signatory_title = db.Column(db.String(255), nullable=True)
    bank_name = db.Column(db.String(255), nullable=True)
    bank_account_number = db.Column(db.String(50), nullable=True)
    commercial_registration = db.Column(db.String(50), nullable=True)
    iban_number = db.Column(db.String(50), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship("Order", backref=db.backref("factory_agreement", uselist=False))

    def __repr__(self):
        return f"<FactoryAgreement {self.company_name} - {self.status}>"

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    quantity_needed = db.Column(db.Integer, nullable=False, default=1)
    quantity_covered = db.Column(db.Integer, nullable=False, default=0)
    min_contribution = db.Column(db.Integer, nullable=False, default=1)
    price_per_carton = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    earnings_per_carton = db.Column(db.Float, nullable=False)
    min_intermediary_contribution = db.Column(db.Integer, nullable=False, default=5)
    intermediary_status = db.Column(db.String(10), nullable=False, default="open")
    payment_method = db.Column(db.String(50), nullable=False, default="الدفع عند الاستلام")
    cities_available = db.Column(db.String(255), nullable=False)
    closing_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    order_status = db.Column(db.String(20), nullable=False, default="مفتوحة")
    completion_rate = db.Column(db.Float, nullable=False, default=0.0)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    admin = db.relationship("User", foreign_keys=[admin_id], backref="created_orders")
    intermediary_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    intermediary = db.relationship("User", foreign_keys=[intermediary_id], backref="assigned_orders")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    zip_file_path = db.Column(db.String(255), nullable=True)  # مسار الملف المضغوط


    def __repr__(self):
        return f"<Order {self.name} - {self.order_status} - وسيط: {self.intermediary_id}>"

class OrderParticipant(db.Model):
    __tablename__ = "order_participants"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    intermediary_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    cartons_requested = db.Column(db.Integer, nullable=False)
    responsible_person = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    tax_number = db.Column(db.String(50), nullable=False)
    commercial_record = db.Column(db.String(255), nullable=True)
    store_sign = db.Column(db.String(255), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default="pending")
    location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="under_review")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    admin_approved = db.Column(db.Boolean, default=False)
    payment_receipt = db.Column(db.String(255), nullable=True)
    
    order = db.relationship("Order", backref=db.backref("participants", lazy="dynamic"))
    intermediary = db.relationship("User", backref=db.backref("managed_participants", lazy="dynamic"))
    # إضافة علاقة جديدة لتخزين مميزات العميل في جدول منفصل
    features = db.relationship("OrderParticipantFeature", backref="participant", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<OrderParticipant {self.store_name} - {self.cartons_requested} كرتونة>"



class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="unread")  # unread أو read
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))


class OrderFeature(db.Model):
    __tablename__ = "order_features"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # اسم الميزة
    description = db.Column(db.Text, nullable=True)  # وصف الميزة

    order = db.relationship("Order", backref=db.backref("features", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Feature {self.name} - Order {self.order_id}>"


class OrderParticipantFeature(db.Model):
    __tablename__ = "order_participant_features"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("order_participants.id"), nullable=False)
    feature_id = db.Column(db.Integer, db.ForeignKey("order_features.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    # علاقة للوصول إلى بيانات الميزة من جدول OrderFeature
    feature = db.relationship("OrderFeature", backref=db.backref("participant_features", lazy=True))

    def __repr__(self):
        return f"<ParticipantFeature participant:{self.participant_id} feature:{self.feature_id} qty:{self.quantity}>"
