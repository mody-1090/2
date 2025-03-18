# app/routes/main_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, WithdrawalRequest, FactoryAgreement, Order, OrderParticipant,  OrderFeature, OrderParticipantFeature ,Notification ,Message ,BlogPost
from werkzeug.utils import secure_filename
import os, uuid
from datetime import datetime
from sqlalchemy import func
from app.services.notification_service import create_notification
from flask import jsonify
from app.forms import AdminRegistrationForm
from app import db, bcrypt , mail, app
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import CustomerRegistrationForm, WithdrawalRequestForm, ApproveFactoryAgreementForm
from sqlalchemy.orm import joinedload
from app.services.database_service import allowed_file, upload_file_to_s3, get_intermediary_folder
import json
from flask_mail import Message as MailMessage
from app.services.email_service import send_support_email, send_ticket_confirmation,   send_contact_email, send_contact_confirmation




main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def home():
    latest_articles = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(6).all()
    return render_template("index.html", latest_articles=latest_articles)


@main_routes.route('/about')
def about():
    return render_template("about.html")

 

# صفحة عرض جميع المدونات
@main_routes.route('/blogs')
def blog_list():
    blogs = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blogs.html', blogs=blogs)

# صفحة عرض مدونة منفصلة بناءً على ID
@main_routes.route('/blogs/<int:blog_id>')
def blog_detail(blog_id):
    
    blog = BlogPost.query.get_or_404(blog_id)

    latest_articles = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(4).all()
    return render_template('blog_detail.html', blog=blog, latest_articles=latest_articles)




@main_routes.route('/delete_all', methods=['POST'])
def delete_all_blogs():
    # حذف جميع المدونات من قاعدة البيانات
    BlogPost.query.delete()
    db.session.commit()
    return redirect(url_for('main_routes.blog_list'))




# صفحة إنشاء المدونة
@main_routes.route('/create', methods=['GET', 'POST'])
def create_blog():

    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية لتعديل الطلبات.", "danger")
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')

        image_url = None
        if image_file and image_file.filename != "":
           image_url = upload_file_to_s3(image_file, user.id)

        # إنشاء المدونة وحفظها في قاعدة البيانات
        blog_post = BlogPost(title=title, content=content, image_path=image_url)
        db.session.add(blog_post)
        db.session.commit()

        return redirect(url_for('main_routes.blog_list'))
    
    return render_template('create_blog.html')


@main_routes.route("/intermediary/support", methods=["GET", "POST"])
def intermediary_support():
    if "user_id" not in session:
        flash("❌ يجب تسجيل الدخول للوصول إلى الدعم الفني.", "danger")
        return redirect(url_for("auth_routes.login"))

    user = User.query.get(session.get("user_id"))
    if not user:
        flash("❌ حدث خطأ أثناء جلب بيانات المستخدم، يرجى تسجيل الدخول مرة أخرى.", "danger")
        return redirect(url_for("auth_routes.login"))

    if request.method == "POST":
        subject = request.form.get("subject")
        message = request.form.get("message")

        if not subject or not message:
            flash("❌ جميع الحقول مطلوبة!", "danger")
            return redirect(url_for("main_routes.intermediary_support"))

        ticket_number = f"TECH-{uuid.uuid4().hex[:8]}"  # ✅ توليد رقم تذكرة فريد

        # ✅ إرسال البريد إلى فريق الدعم
        send_support_email(user.email, user.username, subject, message, ticket_number)

        # ✅ إرسال إشعار للمستخدم
        send_ticket_confirmation(user.email, ticket_number)

        flash(f"✅ تم إرسال طلب الدعم بنجاح! رقم التذكرة: {ticket_number}", "success")
        return redirect(url_for("main_routes.dashboard"))

    return render_template("intermediary_support.html", user=user)








@main_routes.route('/add_self_order', methods=['POST'])
def add_self_order():
    if "user_id" not in session:
        return redirect(url_for('main_routes.login'))

    user = User.query.get(session["user_id"])

    order_id = request.form.get('order_id')
    cartons_requested = int(request.form.get('cartons_requested', 0))
    location = request.form.get('location')
    customer_phone = request.form.get('customer_phone')
    distribution_type = request.form.get('distribution_type', 'توصيل')  # أو قيمة افتراضية

    # الحصول على الملفات من النموذج
    commercial_record = request.files.get("commercial_record")
    store_sign = request.files.get("store_sign")
    payment_receipt = request.files.get("payment_receipt")

    # مسارات الملفات بعد الرفع إلى S3
    commercial_record_path = upload_file_to_s3(commercial_record, user.id) if commercial_record and allowed_file(commercial_record.filename) else None
    store_sign_path = upload_file_to_s3(store_sign, user.id) if store_sign and allowed_file(store_sign.filename) else None
    payment_receipt_path = upload_file_to_s3(payment_receipt, user.id) if payment_receipt and allowed_file(payment_receipt.filename) else None

    # تأكد من وجود الملفات المطلوبة
    if not payment_receipt_path:
        flash('يرجى إرفاق إيصال الدفع.', 'danger')
        return redirect(url_for('main_routes.dashboard'))

    # سجل الطلبية الجديدة للمستخدم نفسه
    new_order_participant = OrderParticipant(
        intermediary_id=user.id,
        order_id=order_id,
        store_name=user.username,  # بما أن المستخدم يطلب لنفسه
        cartons_requested=cartons_requested,
        location=location,
        responsible_person=user.username,
        customer_phone=customer_phone,
        commercial_record_path=commercial_record_path,
        store_sign_path=store_sign_path,
        payment_receipt_path=payment_receipt_path,
        distribution_type=distribution_type,
        status='under_review'  # أو حسب منطقك
    )

    db.session.add(new_order_participant)
    db.session.commit()

    flash('تم تسجيل طلبك بنجاح!', 'success')
    return redirect(url_for('main_routes.dashboard'))






@main_routes.route('/dashboard/home_section')
def dashboard_home_section():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    # استعلام لجلب أحدث 5 إشعارات
    notifications = Notification.query.filter_by(user_id=user.id)\
                    .order_by(Notification.created_at.desc()).limit(5).all()

    # جلب الطلبات التي انضم إليها الوسيط
    participant_orders = db.session.query(Order, OrderParticipant)\
                          .join(OrderParticipant, Order.id == OrderParticipant.order_id)\
                          .filter(OrderParticipant.intermediary_id == user.id)\
                          .order_by(Order.id.desc())\
                          .all()

    # جلب كافة المشاركات الخاصة بالوسيط
    managed_participants = OrderParticipant.query.filter_by(intermediary_id=user.id).all()
    approved_participants = [p for p in managed_participants if p.status == "approved"]
    total_earnings = sum(p.cartons_requested * p.order.earnings_per_carton for p in approved_participants)

    # حساب إجمالي السحوبات (المعلقة والمقبولة)
    pending_or_approved_withdrawals = sum(
        w.amount for w in WithdrawalRequest.query.filter(
            WithdrawalRequest.intermediary_id == user.id,
            WithdrawalRequest.status.in_(["pending", "approved"])
        ).all()
    )
    net_earnings = max(0, total_earnings - pending_or_approved_withdrawals)

    # جلب طلبات السحب بترتيب تنازلي
    withdrawal_requests = WithdrawalRequest.query.filter_by(intermediary_id=user.id)\
                          .order_by(WithdrawalRequest.created_at.desc()).all()

    pending_earnings = sum(w.amount for w in withdrawal_requests if w.status == "pending")
    withdrawn_earnings = sum(w.amount for w in withdrawal_requests if w.status == "approved")
    rejected_earnings = sum(w.amount for w in withdrawal_requests if w.status == "rejected")
    adjusted_total_earnings = total_earnings - pending_earnings - withdrawn_earnings + rejected_earnings

    form = WithdrawalRequestForm()  # تعريف النموذج

    return render_template(
        "partials/home_section.html", 
        user=user, 
        notifications=notifications, 
        participant_orders=participant_orders,
        total_earnings=net_earnings, 
        withdrawal_requests=withdrawal_requests,
        pending_earnings=pending_earnings,
        withdrawn_earnings=withdrawn_earnings,
        adjusted_total_earnings=adjusted_total_earnings,
        form=form
    )


@main_routes.route('/dashboard/orders_section')
def dashboard_orders_section():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    managed_participants = OrderParticipant.query.filter_by(intermediary_id=user.id).all()

    # تقسيم الطلبات حسب الحالة مع الاحتفاظ بجميع البيانات كما في الكود الأصلي
    review_participants = [p for p in managed_participants if p.status == "under_review" and p.cartons_requested > 0]
    approved_participants = [p for p in managed_participants if p.status == "approved" and p.cartons_requested > 0]
    rejected_participants = [p for p in managed_participants if p.status == "rejected"]

    # حساب عدد الصفحات للتقسيم
    per_page = 5
    total_review_pages = (len(review_participants) // per_page) + (1 if len(review_participants) % per_page > 0 else 0)
    total_approved_pages = (len(approved_participants) // per_page) + (1 if len(approved_participants) % per_page > 0 else 0)
    total_rejected_pages = (len(rejected_participants) // per_page) + (1 if len(rejected_participants) % per_page > 0 else 0)

    return render_template(
        "partials/orders_section.html",
        managed_participants=managed_participants,  # ✅ مهمة جدًا لكل تفاصيل القالب
        review_participants=review_participants,
        approved_participants=approved_participants,
        rejected_participants=rejected_participants,
        per_page=per_page,
        total_review_pages=total_review_pages,
        total_approved_pages=total_approved_pages,
        total_rejected_pages=total_rejected_pages
    )
@main_routes.route('/dashboard/add_order_section')
def dashboard_add_order_section():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    # جلب الطلبات التي تم تعيينها للوسيط
    assigned_orders = Order.query.join(OrderParticipant)\
                         .filter(OrderParticipant.intermediary_id == user.id).all()

    form = WithdrawalRequestForm()  # يمكن تغييره إلى CustomerRegistrationForm إذا كان ذلك مناسبًا

    return render_template(
        "partials/add_order_section.html", 
        user=user, 
        assigned_orders=assigned_orders, 
        form=form
    )



@main_routes.route('/open-orders')
def open_orders():
    page = request.args.get('page', 1, type=int)  # رقم الصفحة
    per_page = 10  # عدد الطلبات لكل صفحة

    orders_query = (
        db.session.query(
            Order,
            db.func.coalesce(db.func.sum(OrderParticipant.cartons_requested), 0).label("quantity_covered")
        )
        .outerjoin(OrderParticipant, (Order.id == OrderParticipant.order_id) & (OrderParticipant.status == "approved"))
        .filter(Order.intermediary_id == None)
        .group_by(Order.id)
    )

    paginated_orders = orders_query.paginate(page=page, per_page=per_page, error_out=False)

    # تحويل النتائج إلى قائمة كائنات Order مع إضافة `quantity_covered`
    orders_with_quantity = [
        {
            "order": row[0],  # كائن Order الأصلي
            "quantity_covered": row[1]  # الكمية المغطاة المحسوبة
        }
        for row in paginated_orders.items
    ]

    return render_template("open_orders.html", orders=orders_with_quantity, pagination=paginated_orders)

@main_routes.route('/order/<int:order_id>')
def order_details(order_id):
    order_info = Order.query.get_or_404(order_id)


    return render_template("order_details.html", order=order_info)



@main_routes.route('/update_user_status/<int:user_id>', methods=["POST"])
def update_user_status(user_id):
    if "user_id" not in session or User.query.get(session["user_id"]).role != "admin":
        flash("❌ ليس لديك الصلاحية!", "danger")
        return redirect(url_for("main_routes.dashboard"))
    user = User.query.get_or_404(user_id)
    new_status = request.form.get("new_status")
    if new_status not in ["active", "suspended", "under_review"]:
        flash("⚠️ حالة غير صالحة!", "warning")
        return redirect(url_for("main_routes.dashboard"))
    user.status = new_status
    db.session.commit()
    flash(f"✅ تم تحديث حالة {user.username} إلى {new_status}.", "success")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/intermediary/<int:intermediary_id>')
def intermediary_details(intermediary_id):
    intermediary = User.query.get_or_404(intermediary_id)
    orders = Order.query.filter_by(admin_id=intermediary.id).all()
    clients = OrderParticipant.query.filter_by(intermediary_id=intermediary.id).all()
    total_orders = len(orders)
    total_clients = len(clients)
    total_participations = len(set([p.order_id for p in clients]))
    total_earnings = sum([p.cartons_requested * p.order.earnings_per_carton for p in clients if p.status == "approved"])
    return render_template("intermediary_details.html", intermediary=intermediary, orders=orders,
                           clients=clients, total_orders=total_orders, total_clients=total_clients,
                           total_participations=total_participations, total_earnings=total_earnings)

@main_routes.route('/approve_withdrawal/<int:withdrawal_id>')
def approve_withdrawal(withdrawal_id):
    req = WithdrawalRequest.query.get_or_404(withdrawal_id)
    req.status = "approved"
    db.session.commit()
    flash(f"✅ تم قبول طلب سحب {req.amount} ريال!", "success")
    create_notification(req.intermediary_id, f"✅ تم قبول طلب السحب بقيمة {req.amount:.2f} ريال. سيتم تحويل المبلغ قريبًا.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/reject_withdrawal/<int:withdrawal_id>')
def reject_withdrawal(withdrawal_id):
    req = WithdrawalRequest.query.get_or_404(withdrawal_id)
    req.status = "rejected"
    db.session.commit()
    flash(f"❌ تم رفض طلب سحب {req.amount} ريال.", "danger")
    create_notification(req.intermediary_id, f"❌ تم رفض طلب السحب بقيمة {req.amount:.2f} ريال. يرجى مراجعة التفاصيل.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/revert_withdrawal/<int:withdrawal_id>')
def revert_withdrawal(withdrawal_id):
    req = WithdrawalRequest.query.get_or_404(withdrawal_id)
    req.status = "pending"
    db.session.commit()
    flash(f"🔄 تم إرجاع طلب سحب {req.amount} ريال إلى قيد المراجعة.", "warning")
    create_notification(req.intermediary_id, f"🔄 تم إرجاع طلب السحب بقيمة {req.amount:.2f} ريال إلى قيد المراجعة.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/request_withdrawal', methods=["POST"])
def request_withdrawal():
    if "user_id" not in session:
        flash("❌ يجب تسجيل الدخول لطلب السحب!", "danger")
        return redirect(url_for("auth_routes.login"))
    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)
    total_earnings = db.session.query(
        db.func.sum(OrderParticipant.cartons_requested * Order.earnings_per_carton)
    ).join(Order).filter(
        OrderParticipant.intermediary_id == user_id,
        OrderParticipant.status == "approved"
    ).scalar() or 0.0
    pending_or_approved_withdrawals = sum([
        w.amount for w in WithdrawalRequest.query.filter(
            WithdrawalRequest.intermediary_id == user.id,
            WithdrawalRequest.status.in_(["pending", "approved"])
        ).all()
    ])
    net_earnings = max(0, total_earnings - pending_or_approved_withdrawals)
    if total_earnings <= 0:
        flash("❌ لا توجد أرباح متاحة للسحب.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    
    form = WithdrawalRequestForm()
    if form.validate_on_submit():
        account_holder = form.account_holder.data.strip()
        bank_name = form.bank_name.data.strip()
        account_number = form.account_number.data.strip()
        iban_number = form.iban_number.data.strip()
        if not account_holder or not bank_name or not account_number or not iban_number:
            flash("❌ يرجى إدخال جميع بيانات الحساب البنكي.", "danger")
            return redirect(url_for("main_routes.dashboard"))
        withdrawal_request = WithdrawalRequest(
            intermediary_id=user.id,
            amount=net_earnings,
            account_holder=account_holder,
            bank_name=bank_name,
            account_number=account_number,
            iban_number=iban_number,
            status="pending"
        )
        db.session.add(withdrawal_request)
        flash(f"✅ تم رفع طلب سحب {total_earnings:.2f} ريال بنجاح، وهو قيد المراجعة!", "success")
        create_notification(user.id, f"💰 تم تقديم طلب سحب بقيمة {net_earnings:.2f} ريال وهو الآن قيد المراجعة.")
        db.session.commit()
        return redirect(url_for("main_routes.dashboard"))
    # إذا لم يتحقق النموذج (مثلاً عند إرسال GET أو في حال وجود أخطاء)، نعيد التوجيه كما في النسخة القديمة.
    return redirect(url_for("main_routes.dashboard"))



@main_routes.route('/customer_order/<int:participant_id>')
def customer_order_details(participant_id):
    participant = OrderParticipant.query.get_or_404(participant_id)
    order = participant.order

    # استرجاع ميزات العميل من العلاقة الجديدة
    participant_features = participant.features.all()
    if not participant_features:
        print(f"❌ لا توجد ميزات لهذا العميل (participant_id={participant.id})")
    return render_template("customer_order_details.html", participant=participant, order=order, participant_features=participant_features)

@main_routes.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        flash("يرجى تسجيل الدخول للوصول إلى لوحة التحكم.", "danger")
        return redirect(url_for("auth_routes.login"))
    
    user = User.query.get(session["user_id"])
    
    if user.role == "admin":
        # لتحسين الأداء نستخدم pagination لطلبات العرض (يمكن تعديل per_page حسب الحاجة)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # استعلام الطلبات مع ترتيب تنازلي وpagination
        paginated_orders = Order.query.order_by(Order.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        orders = paginated_orders.items
        
        # تحسين استعلام الوسطاء مع إجراء التجميع داخل SQL
        intermediaries = (
            db.session.query(
                User.id, 
                User.username, 
                User.email, 
                User.phone,
                db.func.count(Order.id).label("total_orders"),
                db.func.count(OrderParticipant.id).label("total_clients"),
                db.func.count(OrderParticipant.order_id.distinct()).label("total_participations"),
                db.func.coalesce(db.func.sum(OrderParticipant.cartons_requested * Order.earnings_per_carton), 0).label("total_earnings")
            )
            .outerjoin(Order, Order.admin_id == User.id)
            .outerjoin(OrderParticipant, OrderParticipant.intermediary_id == User.id)
            .filter(User.role == "intermediary")
            .group_by(User.id)
            .all()
        )
        
        # جلب كافة المشاركات (OrderParticipant) وحساب حالات الطلبات من خلالها
        all_participants = OrderParticipant.query.all()
        pending_orders = [p for p in all_participants if p.status == "under_review"]
        approved_orders = [p for p in all_participants if p.status == "approved"]
        rejected_orders = [p for p in all_participants if p.status == "rejected"]
        
        # تحسين جلب اتفاقيات المصانع بترتيب تنازلي (يمكن استخدام pagination أيضاً إذا زاد العدد)
        factory_agreements = FactoryAgreement.query.order_by(FactoryAgreement.id.desc()).all()
        
        # تحسين جلب طلبات السحب حسب الحالة
        pending_withdrawals = WithdrawalRequest.query.filter_by(status="pending").all()
        approved_withdrawals = WithdrawalRequest.query.filter_by(status="approved").all()
        rejected_withdrawals = WithdrawalRequest.query.filter_by(status="rejected").all()
        
        # إذا كانت طريقة الطلب POST لإنشاء طلبية جديدة
        if request.method == "POST":
            product_name = request.form.get("product_name")
            description = request.form.get("description")
            quantity_needed = request.form.get("quantity")
            price_per_carton = request.form.get("price_per_carton")
            earnings_per_carton = request.form.get("earnings_per_carton")
            min_participation = request.form.get("min_participation")
            intermediary_status = request.form.get("intermediary_status")
            cities_available = request.form.get("city")
            order_deadline = request.form.get("order_deadline")
            delivery_date = request.form.get("delivery_date")
            image_file = request.files.get("product_image")
            zip_file = request.files.get("zip_file")  # استقبال الملف المضغوط
            features = request.form.getlist("features[]")  # ✅ استقبال الميزات

            image_url = None
            zip_file_path = None




            if zip_file and zip_file.filename.endswith(".zip"):
                zip_url = upload_file_to_s3(zip_file, user.id)


            # التحقق من الملف وتحميله باستخدام خدمة S3
            if image_file and allowed_file(image_file.filename):
                image_url = upload_file_to_s3(image_file, user.id)
            
            try:
                quantity_needed = int(quantity_needed)
                price_per_carton = float(price_per_carton)
                earnings_per_carton = float(earnings_per_carton)
                min_participation = int(min_participation)
                closing_date = datetime.strptime(order_deadline, "%Y-%m-%d").date()
                delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()
                total_price = quantity_needed * price_per_carton
            except ValueError:
                flash("⚠️ يرجى إدخال بيانات صحيحة.", "danger")
                return redirect(url_for("main_routes.dashboard"))
            
            new_order = Order(
                name=product_name,
                description=description,
                quantity_needed=quantity_needed,
                price_per_carton=price_per_carton,
                total_price=total_price,
                earnings_per_carton=earnings_per_carton,
                min_contribution=min_participation,
                intermediary_status=intermediary_status,
                cities_available=cities_available,
                closing_date=closing_date,
                delivery_date=delivery_date,
                image_url=image_url,
                admin_id=user.id,
                zip_file_path=zip_url  # رابط الملف المضغوط في S3

             )
            db.session.add(new_order)
            db.session.commit()  # ✅ حفظ الطلبية أولاً

    # ✅ حفظ الميزات إذا تم إدخالها
            for feature_name in features:
             if feature_name.strip():  # التحقق من أن الميزة ليست فارغة
                 new_feature = OrderFeature(order_id=new_order.id, name=feature_name.strip())
             db.session.add(new_feature)

             db.session.commit()  # ✅ حفظ الميزات بعد إضافة الطلبية

            flash("✅ تم إنشاء الطلبية وإضافة المميزات بنجاح!", "success")
            return redirect(url_for("main_routes.dashboard"))

        
        
        return render_template(
            "admin_dashboard.html", 
            user=user, 
            orders=orders,
            pagination=paginated_orders,  # تمرير بيانات pagination إذا أردت إضافتها للقالب
            intermediaries=intermediaries,
            pending_orders=pending_orders,
            approved_orders=approved_orders,
            rejected_orders=rejected_orders,
            factory_agreements=factory_agreements,
            pending_withdrawals=pending_withdrawals,
            approved_withdrawals=approved_withdrawals,
            rejected_withdrawals=rejected_withdrawals,
            messages=Message.query.order_by(Message.created_at.desc()).all()  # جلب الرسائل من الأحدث إلى الأقدم
        )
    
    elif user.role == "intermediary":

                # جلب جميع الطلبات التي انضم إليها الوسيط
        participant_orders = (
            db.session.query(Order, OrderParticipant)
            .join(OrderParticipant, Order.id == OrderParticipant.order_id)
            .filter(OrderParticipant.intermediary_id == user.id)
            .order_by(Order.id.desc())
            .all()
        )

        form = WithdrawalRequestForm()  # إنشاء الفورم وتمريره للقالب
        
        assigned_orders = Order.query.join(OrderParticipant).filter(OrderParticipant.intermediary_id == user.id).all()
        managed_participants = OrderParticipant.query.filter_by(intermediary_id=user.id).all()
        approved_participants = [p for p in managed_participants if p.status == "approved"]
        
        total_earnings = sum([p.cartons_requested * p.order.earnings_per_carton for p in approved_participants])
        
        pending_or_approved_withdrawals = sum([
            w.amount for w in WithdrawalRequest.query.filter(
                WithdrawalRequest.intermediary_id == user.id,
                WithdrawalRequest.status.in_(["pending", "approved"])
            ).all()
        ])
        net_earnings = max(0, total_earnings - pending_or_approved_withdrawals)
        
        withdrawal_requests = WithdrawalRequest.query.filter_by(intermediary_id=user.id)\
            .order_by(WithdrawalRequest.created_at.desc()).all()
        
        pending_earnings = sum([w.amount for w in withdrawal_requests if w.status == "pending"])
        withdrawn_earnings = sum([w.amount for w in withdrawal_requests if w.status == "approved"])
        rejected_earnings = sum([w.amount for w in withdrawal_requests if w.status == "rejected"])
        adjusted_total_earnings = total_earnings - pending_earnings - withdrawn_earnings + rejected_earnings
        
        return render_template(
            "intermediary_dashboard.html", 
            user=user, 
            assigned_orders=assigned_orders, 
            managed_participants=managed_participants, 
            total_earnings=net_earnings,
            withdrawal_requests=withdrawal_requests,
            pending_earnings=pending_earnings,
            withdrawn_earnings=withdrawn_earnings,
            form=form,
            participant_orders=participant_orders,  # ✅ تم تمرير الطلبات المرتبطة بالوسيط

        )
    
    flash("ليس لديك صلاحيات للوصول إلى لوحة التحكم.", "danger")
    return redirect(url_for("main_routes.home"))


@main_routes.route('/create_factory_agreement', methods=["POST"])
def create_factory_agreement():
    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية لإنشاء الاتفاقيات.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    order_id = request.form.get("order_id")
    company_name = request.form.get("company_name")
    carton_price = request.form.get("ccarton_price")
    order = Order.query.get(order_id)
    if not order:
        flash("❌ الطلبية غير موجودة.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    agreement_link = str(uuid.uuid4())
    new_agreement = FactoryAgreement(
        order_id=order_id,
        company_name=company_name,
        agreement_link=f"factory_agreement/{agreement_link}",
        status="pending"
    )
    db.session.add(new_agreement)
    db.session.commit()
    flash(f"✅ تم إنشاء الاتفاق بنجاح! رابط الاتفاق: {new_agreement.agreement_link}", "success")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/factory_agreement/<string:agreement_link>')
def factory_agreement(agreement_link):
    agreement = FactoryAgreement.query.filter_by(agreement_link=f"factory_agreement/{agreement_link}").first_or_404()
    form = ApproveFactoryAgreementForm()  # إنشاء النموذج هنا
    return render_template("factory_agreement.html", agreement=agreement, form=form)

@main_routes.route('/approve_factory_agreement/<int:agreement_id>', methods=["GET", "POST"])
def approve_factory_agreement(agreement_id):
    agreement = FactoryAgreement.query.get_or_404(agreement_id)
    form = ApproveFactoryAgreementForm()
    
    if form.validate_on_submit():
        # استلام البيانات من الحقول الظاهرة
        signatory_name = form.signatory_name.data.strip()
        signatory_title = form.signatory_title.data.strip()
        # الحقول المخفية تُستخدم بالقيم الافتراضية المُعطاة
        bank_name = form.bank_name.data.strip()
        bank_account_number = form.bank_account_number.data.strip()
        iban_number = form.iban_number.data.strip()
        commercial_registration = form.commercial_registration.data.strip()
        
        if not signatory_name or not signatory_title:
            flash("❌ يرجى إدخال اسم الموقع والصفة.", "danger")
            return redirect(request.referrer or url_for("factory_agreement", agreement_id=agreement.id))
        try:
            agreement.signatory_name = signatory_name
            agreement.signatory_title = signatory_title
            agreement.bank_name = bank_name
            agreement.bank_account_number = bank_account_number
            agreement.iban_number = iban_number
            # إذا أردت تخزين السجل التجاري، يمكنك إضافته إلى النموذج أو تجاهله حسب التصميم
            agreement.commercial_registration = commercial_registration
            agreement.status = "approved"
            agreement.approval_date = datetime.utcnow()
            db.session.commit()
            flash("✅ تم قبول الاتفاقية وإضافة البيانات البنكية بنجاح!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ حدث خطأ أثناء حفظ البيانات: {e}", "danger")
        return redirect(request.referrer or url_for("factory_agreement", agreement_id=agreement.id))
    
    return render_template("factory_agreement.html", agreement=agreement, form=form)


@main_routes.route('/update_order/<int:order_id>', methods=["POST"])
def update_order(order_id):
    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية لتعديل الطلبات.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    order = Order.query.get_or_404(order_id)
    name = request.form.get("name")
    description = request.form.get("description")
    quantity_needed = request.form.get("quantity_needed")
    price_per_carton = request.form.get("price_per_carton")
    min_contribution = request.form.get("min_contribution")
    earnings_per_carton = request.form.get("earnings_per_carton")
    cities_available = request.form.get("cities_available")
    closing_date = request.form.get("closing_date")
    delivery_date = request.form.get("delivery_date")
    image_file = request.files.get("product_image")



    if image_file and allowed_file(image_file.filename):
          image_url = upload_file_to_s3(image_file, user.id)
          if image_url:
              order.image_url = image_url

        
    try:
        order.name = name
        order.description = description
        order.quantity_needed = int(quantity_needed)
        order.price_per_carton = float(price_per_carton)
        order.min_contribution = int(min_contribution)
        order.earnings_per_carton = float(earnings_per_carton)
        order.cities_available = cities_available
        order.closing_date = datetime.strptime(closing_date, "%Y-%m-%d").date()
        order.delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()
        db.session.commit()
        flash(f"✅ تم تحديث الطلب {order.id} بنجاح!", "success")
    except ValueError:
        flash("❌ حدث خطأ أثناء التحديث. تأكد من صحة القيم المدخلة.", "danger")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/approve_order/<int:participant_id>', methods=["POST"])
def approve_order(participant_id):
    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية للموافقة على الطلبات.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    participant = OrderParticipant.query.get_or_404(participant_id)
    participant.status = "approved"
    db.session.commit()
    flash(f"✅ تم قبول الطلب للعميل {participant.store_name}!", "success")
    create_notification(participant.intermediary_id, f"✅ تم قبول طلب العميل {participant.store_name}.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/delete-order/<int:order_id>', methods=["POST"])
def delete_order(order_id):
    if "user_id" not in session:
        flash("يرجى تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("ليس لديك صلاحيات لحذف الطلبات.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    order = Order.query.get_or_404(order_id)
    try:
        db.session.delete(order)
        db.session.commit()
        flash("تم حذف الطلبية بنجاح!", "success")
    except Exception as e:
        flash(f"حدث خطأ أثناء الحذف: {str(e)}", "danger")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/join_order/<int:order_id>', methods=["POST"])
def join_order(order_id):
    if "user_id" not in session:
        flash("يجب تسجيل الدخول للانضمام إلى الطلبية.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "intermediary":
        flash("فقط الوسطاء يمكنهم الانضمام إلى الطلبية.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    order = Order.query.get_or_404(order_id)
    existing_participant = OrderParticipant.query.filter_by(order_id=order.id, intermediary_id=user.id).first()
    if existing_participant:
        flash("✅ أنت بالفعل وسيط لهذه الطلبية!", "warning")
        return redirect(url_for("main_routes.order_details", order_id=order.id))
    new_participant = OrderParticipant(
        order_id=order.id,
        intermediary_id=user.id,
        store_name=f"وسيط: {user.username}",
        cartons_requested=0,
        payment_status="pending",
        location="غير محدد",
        tax_number="غير متوفر",
        commercial_record=None,
        store_sign=None,
        status="under_review"
    )
    try:
        db.session.add(new_participant)
        db.session.commit()
        flash(f"✅ تم انضمامك كوسيط للطلبية {order.name}!", "success")
        create_notification(user.id, f"✅ لقد انضممت إلى الطلبية {order.name}.")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ حدث خطأ أثناء الانضمام: {str(e)}", "danger")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/customer_registration/<int:intermediary_id>/<int:order_id>', methods=["GET", "POST"])
def customer_registration(intermediary_id, order_id):
    intermediary = User.query.get_or_404(intermediary_id)
    order = Order.query.get_or_404(order_id)
    form = CustomerRegistrationForm()

    if form.validate_on_submit():
        # استخدم البيانات من النموذج كما في الكود القديم
        store_name = form.store_name.data.strip()
        cartons_requested = form.cartons_requested.data
        location = form.location.data.strip()
        responsible_person = form.responsible_person.data
        customer_phone = form.customer_phone.data
        tax_number = form.tax_number.data
        commercial_record = form.commercial_record.data
        store_sign = form.store_sign.data
        payment_receipt = form.payment_receipt.data

        # تحقق من وجود الحقول المطلوبة (سيتم التحقق من DataRequired تلقائيًا لكن نحتفظ بالمنطق الحالي)
        if not store_name or not location or not cartons_requested or not tax_number or not payment_receipt:
            flash("⚠️ يرجى ملء جميع الحقول المطلوبة، بما في ذلك إيصال الدفع.", "warning")
            return redirect(url_for("main_routes.customer_registration", intermediary_id=intermediary_id, order_id=order_id))

        try:
            cartons_requested = int(cartons_requested)
            if cartons_requested < order.min_contribution:
                flash(f"⚠️ الحد الأدنى للطلب هو {order.min_contribution} كرتون.", "warning")
                return redirect(url_for("main_routes.customer_registration", intermediary_id=intermediary_id, order_id=order_id))
        except ValueError:
            flash("⚠️ عدد الكراتين يجب أن يكون رقمًا صحيحًا موجبًا.", "warning")
            return redirect(url_for("main_routes.customer_registration", intermediary_id=intermediary_id, order_id=order_id))

        intermediary_folder = get_intermediary_folder(intermediary_id)
        commercial_record_path = None
        store_sign_path = None
        payment_receipt_path = None

        # حفظ الملفات كما في الكود القديم
        
        if commercial_record and allowed_file(commercial_record.filename):
           commercial_record_path = upload_file_to_s3(commercial_record, intermediary.id)

        if store_sign and allowed_file(store_sign.filename):
           store_sign_path = upload_file_to_s3(store_sign, intermediary.id)

        if  payment_receipt and allowed_file(payment_receipt.filename):
            payment_receipt_path = upload_file_to_s3(payment_receipt, intermediary.id)





        new_participant = OrderParticipant(
            order_id=order.id,
            intermediary_id=intermediary.id,
            store_name=store_name,
            cartons_requested=cartons_requested,
            location=location,
            responsible_person=responsible_person,
            customer_phone=customer_phone,
            tax_number=tax_number,
            commercial_record=commercial_record_path,
            store_sign=store_sign_path,
            payment_receipt=payment_receipt_path,  
            status="under_review"
        )
        db.session.add(new_participant)
        order.quantity_covered += cartons_requested
        db.session.commit()
        flash("✅ تم تسجيل طلبك بنجاح، وهو الآن قيد المراجعة!", "success")
        create_notification(f"{intermediary.id}", f"✅ تم تسجيل العميل '{store_name}' في الطلبية {order.name} بنجاح!")
        return redirect(url_for("main_routes.customer_order_details", participant_id=new_participant.id))

    return render_template("customer_registration.html", intermediary=intermediary, order=order, form=form)


@main_routes.route('/add_customer', methods=["POST"])
def add_customer():
    if "user_id" not in session:
        flash("❌ يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))

    user = User.query.get(session["user_id"])
    order_id = request.form.get("order_id")
    if not order_id or not order_id.isdigit():
        flash("⚠️ يرجى اختيار طلبية صالحة.", "warning")
        return redirect(url_for("main_routes.dashboard"))

    order_id = int(order_id)
    order = Order.query.get_or_404(order_id)
    participation = OrderParticipant.query.filter_by(order_id=order_id, intermediary_id=user.id).first()
    if not participation:
        flash("🚫 يجب عليك الانضمام أولاً إلى الطلبية قبل إضافة العملاء.", "danger")
        return redirect(url_for("main_routes.dashboard"))

    store_name = request.form.get("store_name", "").strip()
    cartons_requested = request.form.get("cartons_requested", "0")
    location = request.form.get("location", "").strip()
    responsible_person = request.form.get("responsible_person")
    customer_phone = request.form.get("customer_phone")
    tax_number = request.form.get("tax_number")
    
    try:
        cartons_requested = int(cartons_requested)
        if cartons_requested < order.min_contribution:
            flash(f"❌ الحد الأدنى للمشاركة هو {order.min_contribution} كرتون!", "danger")
            return redirect(url_for("main_routes.dashboard"))
    except ValueError:
        flash("⚠️ عدد الكراتين يجب أن يكون رقماً صحيحاً موجباً.", "warning")
        return redirect(url_for("main_routes.dashboard"))

    total_payment = cartons_requested * order.price_per_carton
    intermediary_folder = get_intermediary_folder(user.id)

    commercial_record = request.files.get("commercial_record")
    store_sign = request.files.get("store_sign")
    payment_receipt = request.files.get("payment_receipt")
    distribution_type = request.form.get("distribution_type")  # طريقة التوزيع

    commercial_record_path = None
    store_sign_path = None
    payment_receipt_path = None

    if commercial_record and allowed_file(commercial_record.filename):
        commercial_record_path = upload_file_to_s3(commercial_record, user.id)

    if store_sign and allowed_file(store_sign.filename):
        store_sign_path = upload_file_to_s3(store_sign, user.id)

    if payment_receipt and allowed_file(payment_receipt.filename):
        payment_receipt_path = upload_file_to_s3(payment_receipt, user.id)

    # إنشاء سجل العميل الأساسي في جدول OrderParticipant
    new_participant = OrderParticipant(
        order_id=order.id,
        intermediary_id=user.id,
        store_name=store_name,
        cartons_requested=cartons_requested,
        location=location,
        responsible_person=responsible_person,
        customer_phone=customer_phone,
        tax_number=tax_number,
        commercial_record=commercial_record_path,
        store_sign=store_sign_path,
        payment_receipt=payment_receipt_path,
        payment_status="paid",
        status="under_review"
    )
    db.session.add(new_participant)
    db.session.commit()  # حفظ بيانات العميل أولاً

    # حفظ بيانات المميزات بشكل منفصل إذا كان توزيع الكمية "مخصص"
    if distribution_type == "custom":
        # قراءة كل حقل يبدأ بـ "feature_quantities["
        for key in request.form:
            if key.startswith("feature_quantities[") and key.endswith("]"):
                feature_id_str = key[len("feature_quantities["):-1]
                try:
                    feature_id_int = int(feature_id_str)
                except ValueError:
                    continue
                try:
                    quantity_int = int(request.form.get(key, 0))
                except ValueError:
                    quantity_int = 0
                # حفظ السجل فقط إذا كانت الكمية أكبر من صفر
                if quantity_int > 0:
                    participant_feature = OrderParticipantFeature(
                        participant_id=new_participant.id,
                        feature_id=feature_id_int,
                        quantity=quantity_int
                    )
                    db.session.add(participant_feature)
        db.session.commit()  # حفظ بيانات المميزات

    flash(f"✅ تم تسجيل العميل '{store_name}' في الطلبية {order.name} بنجاح!", "success")
    create_notification(user.id, f"✅ تم تسجيل العميل '{store_name}' في الطلبية {order.name} بنجاح!")
    return redirect(url_for("main_routes.customer_order_details", participant_id=new_participant.id))


@main_routes.route('/reject_order/<int:participant_id>', methods=["POST"])
def reject_order(participant_id):
    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية لرفض الطلبات.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    participant = OrderParticipant.query.get_or_404(participant_id)
    participant.status = "rejected"
    participant.cartons_requested = 0
    db.session.commit()
    flash(f"❌ تم رفض الطلب للعميل {participant.store_name}!", "danger")
    create_notification(participant.intermediary_id, f"❌ تم رفض طلب العميل {participant.store_name}.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/revert_order/<int:participant_id>', methods=["POST"])
def revert_order(participant_id):
    if "user_id" not in session:
        flash("يجب تسجيل الدخول.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("❌ ليس لديك الصلاحية لإجراء هذه العملية.", "danger")
        return redirect(url_for("main_routes.dashboard"))
    participant = OrderParticipant.query.get_or_404(participant_id)
    participant.status = "under_review"
    db.session.commit()
    flash(f"🔄 تم إرجاع الطلب للعميل {participant.store_name} إلى قيد المراجعة!", "warning")
    create_notification(participant.intermediary_id, f"🔄 تم إرجاع طلب العميل {participant.store_name} إلى قيد المراجعة.")

    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/intermediary_training')
def intermediary_training():
    return render_template("intermediary_training.html")

@main_routes.route('/intermediary_dashboard')
def intermediary_dashboard():
    if "user_id" not in session:
        flash("يرجى تسجيل الدخول للوصول إلى لوحة التحكم.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    if user.role != "intermediary":
        flash("ليس لديك صلاحيات للوصول إلى هذه الصفحة.", "danger")
        return redirect(url_for("main_routes.home"))
    assigned_orders = Order.query.filter_by(intermediary_id=user.id).all()
    managed_participants = OrderParticipant.query.filter_by(intermediary_id=user.id).all()
    total_earnings = sum(
        [participant.cartons_requested * participant.order.earnings_per_carton for participant in managed_participants if participant.status == "approved"]
    )
    return render_template(
        "intermediary_dashboard.html",
        user=user,
        assigned_orders=assigned_orders,
        managed_participants=managed_participants,
        total_earnings=total_earnings
    )

@main_routes.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_content = request.form.get("message")

        if not name or not email or not message_content:
            flash("❌ جميع الحقول مطلوبة!", "danger")
            return redirect(url_for("main_routes.contact"))
        # ✅ توليد رقم تذكرة فريد
        ticket_number = f"INFO-{uuid.uuid4().hex[:8]}"

        # ✅ حفظ الرسالة في قاعدة البيانات
        new_message = Message(name=name, email=email, content=message_content)
        db.session.add(new_message)
        db.session.commit()

        # ✅ إرسال البريد إلى فريق التواصل مع تمرير `ticket_number`
        send_contact_email(name, email, message_content, ticket_number)

        # ✅ إرسال تأكيد للمستخدم مع تمرير `ticket_number`
        send_contact_confirmation(name, email, ticket_number)

        flash("✅ تم إرسال رسالتك بنجاح!", "success")
        return redirect(url_for("main_routes.contact"))

    return render_template("contact.html")


@main_routes.route('/assign-intermediary/<int:order_id>', methods=["POST"])
def assign_intermediary(order_id):
    if "user_id" not in session or User.query.get(session["user_id"]).role != "admin":
        flash("يجب تسجيل الدخول كمدير لإدارة الوسطاء", "danger")
        return redirect(url_for("auth_routes.login"))
    order = Order.query.get_or_404(order_id)
    intermediary_id = request.form.get("intermediary_id")
    if not intermediary_id:
        flash("يرجى تحديد وسيط!", "danger")
        return redirect(url_for("main_routes.dashboard"))
    order.intermediary_id = intermediary_id
    db.session.commit()
    flash("تم تعيين الوسيط بنجاح!", "success")
    return redirect(url_for("main_routes.dashboard"))

@main_routes.route('/terms')
def terms():
    return render_template("terms.html")

@main_routes.route('/privacy')
def privacy():
    return render_template("privacy.html")



@main_routes.route('/profile')
def profile():
    if "user_id" not in session:
        flash("يرجى تسجيل الدخول للوصول إلى الصفحة الشخصية.", "danger")
        return redirect(url_for("auth_routes.login"))
    user = User.query.get(session["user_id"])
    user_orders = Order.query.filter_by(intermediary_id=user.id).all()
    return render_template("profile.html", user=user, user_orders=user_orders)


@main_routes.route('/update_profile', methods=["POST"])
def update_profile():
    if "user_id" not in session:
        flash("❌ يجب تسجيل الدخول أولًا.", "danger")
        return redirect(url_for("auth_routes.login"))

    user = User.query.get(session["user_id"])
    if user:
        user.username = request.form.get("username", user.username)
        user.email = request.form.get("email", user.email)
        user.phone = request.form.get("phone", user.phone)
        db.session.commit()
        flash("✅ تم تحديث المعلومات بنجاح!", "success")
    else:
        flash("❌ حدث خطأ أثناء التحديث.", "danger")

    return redirect(url_for("main_routes.profile"))



@main_routes.route('/mark_notifications_read', methods=["POST"])
def mark_notifications_read():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get(session["user_id"])
    if user:
        for notification in user.notifications.filter_by(status="unread").all():
            notification.status = "read"
        db.session.commit()
        return jsonify({"message": "تم تحديث الإشعارات إلى مقروءة."})

    return jsonify({"error": "User not found"}), 404





@main_routes.app_errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404

@main_routes.app_errorhandler(500)
def internal_server_error(error):
    return render_template("errors/500.html"), 500


@main_routes.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        hashed_password =generate_password_hash(form.password.data, method="pbkdf2:sha256")
        admin = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            phone=form.phone.data,
            role="admin"  # تحديد دور المسؤول


        )
        db.session.add(admin)
        db.session.commit()
        flash("تم تسجيل المسؤول بنجاح!", "success")
        return redirect(url_for('main_routes.home'))  # إعادة التوجيه للصفحة الرئيسية
    return render_template('register_admin.html', form=form)


