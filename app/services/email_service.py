from flask_mail import Message
from app import mail, app

def send_support_email(user_email, user_name, subject, message_content, ticket_number):
    """إرسال البريد إلى فريق الدعم الفني"""
    msg = Message(
        subject=f"📩 {subject} - تذكرة دعم #{ticket_number}",
        sender=app.config["MAIL_SUPPORT"],  # ✅ بريد الدعم الفني
        recipients=[app.config["MAIL_SUPPORT"]],  # ✅ إرسال لفريق الدعم
        body=f"""تم استلام طلب دعم جديد من:
🔹 الاسم: {user_name}
📧 البريد: {user_email}

📩 عنوان الطلب: {subject}
📩 تفاصيل الرسالة:
{message_content}

🔎 رقم التذكرة: {ticket_number}
"""
    )
    mail.send(msg)




def send_ticket_confirmation(user_email, ticket_number):
    """إرسال تأكيد فتح تذكرة دعم للمستخدم"""
    msg = Message(
        subject=f"✅ تم فتح تذكرة الدعم #{ticket_number}",
        sender=app.config["MAIL_SUPPORT"],  # ✅ بريد الدعم الفني
        recipients=[user_email],
        body=f"""شكرًا لتواصلك معنا! تم فتح تذكرة جديدة برقم #{ticket_number}.
سيقوم فريق الدعم الفني بمراجعة طلبك والرد عليك قريبًا.

🔎 رقم التذكرة: {ticket_number}

📧 لا تتردد في الرد على هذه الرسالة إذا كنت بحاجة إلى مزيد من التفاصيل.
"""
    )
    mail.send(msg)




# ✅ إرسال بريد إلى فريق التواصل عند استلام طلب تواصل جديد
def send_contact_email(name, email, message_content, ticket_number):
    """إرسال بريد إلى فريق التواصل عند استلام طلب تواصل جديد"""
    try:
        msg = Message(
            subject=f"📩 طلب تواصل جديد #{ticket_number}",
            sender=app.config["MAIL_INFO"],  # ✅ بريد info
        recipients=[app.config["MAIL_INFO"]],  # ✅ إرسال لفريق المراسلات العامة
        )
        msg.body = f"""
تم استلام طلب تواصل جديد من:
🔹 الاسم: {name}
📧 البريد: {email}

📩 تفاصيل الرسالة:
{message_content}

🔎 رقم التذكرة: {ticket_number}
"""
        mail.send(msg)
        print(f"✅ تم إرسال بريد 'تواصل معنا' لفريق التواصل - رقم التذكرة {ticket_number}")
    except Exception as e:
        print(f"❌ فشل إرسال بريد 'تواصل معنا' لفريق التواصل: {str(e)}")

# ✅ إرسال تأكيد للمستخدم بعد استلام طلبه
def send_contact_confirmation(name, email, ticket_number):
    """إرسال تأكيد للمستخدم عند استلام طلبه"""
    try:
        msg = Message(
            subject=f"✅ تم استلام طلبك #{ticket_number}",
            sender=app.config["MAIL_INFO"],  # ✅ بريد info
            recipients=[email]  # إرسال للمستخدم
        )
        msg.body = f"""
مرحبًا {name}،

تم استلام طلبك وسنقوم بالرد عليك قريبًا.

🔎 رقم التذكرة: {ticket_number}

شكراً لتواصلك معنا!
jumlat.com
"""
        mail.send(msg)
        print(f"✅ تم إرسال تأكيد 'تواصل معنا' إلى المستخدم {email} - رقم التذكرة {ticket_number}")
    except Exception as e:
        print(f"❌ فشل إرسال تأكيد 'تواصل معنا' إلى المستخدم {email}: {str(e)}")
