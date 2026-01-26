# ---------------- دالة الإرسال الذكية (تحل مشاكل التسجيل) ----------------
def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    """إرسال بريد إلكتروني للأستاذ (نسخة ذكية للتعامل مع اختلافات البيانات)"""
    try:
        # 1. تحميل البيانات
        df_prof_memos = load_prof_memos()
        
        # 2. البحث المرن عن الأستاذ
        # محاولة البحث بالاسم المطابق تماماً
        prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        
        # إذا لم نجد، نبحث عن الأسم التي تحتوي على جزء من الاسم (للتعامل مع اختلاف الألقاب)
        if prof_row.empty:
            # نحذف الألقاب الشائعة "الأستاذ"، "د."، "أ.د" للمحاولة
            clean_name = prof_name.strip().replace("الأستاذ", "").replace("د.", "").replace("أ.د", "").strip()
            if clean_name:
                prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.contains(clean_name, case=False, na=False)]
        
        if prof_row.empty:
            error_msg = f"فشل الإرسال: لم يتم العثور على البريد للأستاذ <b>{prof_name}</b>.<br>يرجى التأكد من تطابق اسمه في جدول مذكرات الأساتذة."
            logger.error(f"Email Error: Professor {prof_name} not found in Prof Memos sheet.")
            return False, error_msg

        # أخذ الصف الأول (إذا وجدنا تطابق جزئي)
        prof_data = prof_row.iloc[0]
        
        # 3. البحث الذكي عن عمود الإيميل
        prof_email = ""
        possible_email_cols = ["البريد الإلكتروني", "الإيميل", "email", "Email"]
        for col in possible_email_cols:
            if col in prof_data.index:
                val = str(prof_data[col]).strip()
                if val and val != "nan":
                    prof_email = val
                    break
        
        if "@" not in prof_email:
            error_msg = f"فشل الإرسال: الأستاذ <b>{prof_name}</b> موجود، ولكن عمود البريد الإلكتروني فارغ أو غير صحيح.<br>عمود البريد الموجود: {prof_data.get('البريد الإلكتروني', prof_data.get('الإيميل', 'غير موجود'))}"
            logger.error(f"Email Error: Invalid email for Prof {prof_name}: {prof_email}")
            return False, error_msg

        # 4. حساب الإحصائيات
        total_memos = len(prof_row)
        registered_memos = len(prof_row[prof_row["تم التسجيل"].astype(str).str.strip() == "نعم"])
        remaining_memos = total_memos - registered_memos
        
        used_passwords = []
        available_passwords = []
        
        for idx, row in prof_row.iterrows():
            password = str(row.get("كلمة سر التسجيل", "")).strip()
            if password:
                if str(row.get("تم التسجيل", "")).strip() == "نعم":
                    used_passwords.append(f"✅ {password}")
                else:
                    available_passwords.append(f"⏳ {password}")
        
        # 5. تجهيز بيانات الطلاب
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('إسم', student1.get('إسم', ''))
        student2_info = ""
        
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('إسم', student2.get('إسم', ''))
            student2_info = f"\n👤 **الطالب الثاني:** {s2_lname} {s2_fname}"
        
        passwords_list = "\n".join(used_passwords + available_passwords) if (used_passwords or available_passwords) else "لا توجد كلمات سر مسجلة"
        
        # 6. بناء الإيميل
        email_body = f"""
<html dir="rtl">
<head>
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
        .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
        .header h2 {{ margin: 0; }}
        .content {{ line-height: 1.8; color: #333; }}
        .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }}
        .stats-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        .highlight {{ color: #256D85; font-weight: bold; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ تسجيل مذكرة جديدة</h2>
        </div>
        
        <div class="content">
            <p>تحية طيبة وبعد : الأستاذ(ة) الفاضل(ة) <span class="highlight">{prof_name}</span>،</p>
            
            <p>نحيطكم علماً بأنه تم تسجيل مذكرة جديدة تحت إشرافكم:</p>
            
            <div class="info-box">
                <p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p>
                <p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p>
                <p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p>
                <p>👤 <strong>الطالب الأول:</strong> {s1_lname} {s1_fname}{student2_info}</p>
                <p>🕒 <strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="stats-box">
                <h3 style="color: #256D85; margin-top: 0;">📊 إحصائيات مذكراتك:</h3>
                <ul>
                    <li>📝 <strong>إجمالي المذكرات:</strong> {total_memos}</li>
                    <li>✅ <strong>المذكرات المسجلة:</strong> {registered_memos}</li>
                    <li>⏳ <strong>المذكرات المتبقية:</strong> {remaining_memos}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3 style="color: #256D85; margin-top: 0;">🔑 كلمات السر:</h3>
                <ul style="white-space: pre-line;">{passwords_list}</ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">للاستفسار أو الدعم، يرجى التواصل مع السيد مسؤول الميدان الدكتور رفاف لخضر.</p>
        </div>
        
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
            <p>كلية الحقوق والعلوم السياسية</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة جديدة - رقم {memo_info['رقم المذكرة']}"
        
        html_part = MIMEText(email_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # إرسال الإيميل
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ تم إرسال بريد إلكتروني للأستاذ {prof_name} على {prof_email}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False, f"خطأ تقني أثناء الإرسال: {str(e)}"