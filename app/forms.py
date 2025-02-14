from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, HiddenField, SubmitField

class AdminRegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    phone = StringField('رقم الهاتف', validators=[Length(max=20)])
    submit = SubmitField('تسجيل المسؤول')



# نستخدم StringField لعدد الكراتين للحفاظ على نفس أسلوب التحويل اليدوي
class CustomerRegistrationForm(FlaskForm):
    store_name = StringField("اسم المتجر أو العميل", validators=[DataRequired()])
    cartons_requested = StringField("عدد الكراتين المطلوبة", validators=[DataRequired()])
    location = StringField("موقع العميل", validators=[DataRequired()])
    responsible_person = StringField("اسم المسؤول في المتجر")
    customer_phone = StringField("رقم جوال العميل", validators=[DataRequired()])
    tax_number = StringField("الرقم الضريبي", validators=[DataRequired()])
    commercial_record = FileField("صورة السجل التجاري", validators=[DataRequired()])
    store_sign = FileField("صورة لوحة المحل", validators=[DataRequired()])
    payment_receipt = FileField("إيصال الدفع", validators=[DataRequired()])
    submit = SubmitField("تسجيل الطلبية")




class WithdrawalRequestForm(FlaskForm):
    account_holder = StringField("اسم صاحب الحساب", validators=[DataRequired()])
    bank_name = StringField("اسم البنك", validators=[DataRequired()])
    account_number = StringField("رقم الحساب البنكي", validators=[DataRequired()])
    iban_number = StringField("رقم الآيبان", validators=[DataRequired()])
    submit = SubmitField("سحب الأرباح المتاحة")





class RegistrationForm(FlaskForm):
    username = StringField("اسم المستخدم", validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField("البريد الإلكتروني", validators=[DataRequired(), Email()])
    phone = StringField("رقم الهاتف")  # اختياري
    password = PasswordField("كلمة المرور", validators=[DataRequired(), Length(min=6)])
    role = HiddenField("دور المستخدم", default="intermediary")  # قيمة مخفية دائمًا "intermediary"
    submit = SubmitField("إنشاء حساب")




class ApproveFactoryAgreementForm(FlaskForm):
    # الحقول الظاهرة للمستخدم
    signatory_name = StringField("اسم الموقع الرسمي", validators=[DataRequired()])
    signatory_title = StringField("الصفة", validators=[DataRequired()])
    # الحقول المخفية بالقيم الثابتة
    bank_name = HiddenField(default="الراجحي / شركة محمد حسن محمد الحربي لتجارة الجملة والتجزئة")
    bank_account_number = HiddenField(default="589000010006086204363")
    iban_number = HiddenField(default="SA9480000589608016204363")
    commercial_registration = HiddenField(default="1009193632")
    submit = SubmitField("الموافقة وإرسال البيانات البنكية")
