import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرة ماستر", page_icon="🎓", layout="centered")

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; max-width: 750px; margin:auto;}
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color:#ffffff !important; }
button { background-color:#256D85 !important; color:white !important; border:none !important; padding:10px 20px !important; border-radius:6px !important; }
button:hover { background-color:#2C89A0 !important; }
.message { font-size:18px; font-weight:bold; text-align:center; margin:10px 0; color:#FFFFFF;}
.logout-btn { background-color:#8B0000 !important; }
.logout-btn:hover { background-color:#A52A2A !important; }
.success-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.error-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
.info-msg { color: #FFFFFF; padding: 15px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

# ---------------- Email Configuration ----------------
EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    """تحويل رقم العمود إلى حرف (يدعم أكثر من 26 عمود)"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    """تنقية المدخلات من الأحرف الخطرة"""
    if not text:
        return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    cleaned = str(text).strip()
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    return cleaned

def validate_username(username):
    """التحقق من صحة اسم المستخدم"""
    username = sanitize_input(username)
    if not username:
        return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    """التحقق من صحة رقم المذكرة"""
    note_number = sanitize_input(note_number)
    if not note_number:
        return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20:
        return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

# ---------------- تحميل البيانات ----------------
@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID, 
            range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            logger.error("لا توجد بيانات في صفحة الطلاب")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} طالب")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات الطلاب: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID, 
            range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            logger.error("لا توجد بيانات في صفحة المذكرات")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=PROF_MEMOS_SHEET_ID, 
            range=PROF_MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            logger.error("لا توجد بيانات في صفحة المذكرات - الأساتذة")
            return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        logger.info(f"تم تحميل {len(df)} مذكرة للأساتذة")
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        st.error(f"❌ خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    """مسح الكاش وإعادة تحميل البيانات"""
    st.cache_data.clear()
    logger.info("تم مسح الكاش")

# ---------------- إرسال البريد الإلكتروني ----------------
def send_email_to_professor(prof_email, prof_name, memo_info, student1, student2=None):
    """إرسال بريد إلكتروني للأستاذ عند تسجيل مذكرة"""
    try:
        df_prof_memos = load_prof_memos()
        prof_memos = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total_memos = len(prof_memos)
        registered_memos = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        remaining_memos = total_memos - registered_memos
        
        used_passwords = []
        available_passwords = []
        
        for idx, row in prof_memos.iterrows():
            password = str(row.get("كلمة سر التسجيل", "")).strip()
            if password:
                if str(row.get("تم التسجيل", "")).strip() == "نعم":
                    used_passwords.append(f"✅ {password}")
                else:
                    available_passwords.append(f"⏳ {password}")
        
        student2_info = ""
        if student2 is not None:
            student2_info = f"\n👤 **الطالب الثاني:** {student2['اللقب']} {student2['الإسم']}"
        
        passwords_list = "\n".join(used_passwords + available_passwords) if (used_passwords or available_passwords) else "لا توجد كلمات سر مسجلة"
        
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
            <p>السلام عليكم الأستاذ(ة) الفاضل(ة) <span class="highlight">{prof_name}</span>،</p>
            
            <p>نحيطكم علماً بأنه تم تسجيل مذكرة جديدة تحت إشرافكم:</p>
            
            <div class="info-box">
                <p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p>
                <p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p>
                <p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p>
                <p>👤 <strong>الطالب الأول:</strong> {student1['اللقب']} {student1['الإسم']}{student2_info}</p>
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
            
            <p style="margin-top: 20px; color: #666;">للاستفسار أو الدعم، يرجى التواصل مع إدارة الكلية.</p>
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
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ تم إرسال بريد إلكتروني للأستاذ {prof_name} على {prof_email}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال البريد الإلكتروني: {str(e)}")
        return False, f"فشل إرسال البريد: {str(e)}"

# ---------------- التحقق ----------------
def verify_student(username, password, df_students):
    """التحقق من بيانات الطالب"""
    valid, result = validate_username(username)
    if not valid:
        logger.warning(f"محاولة دخول بـ username غير صالح: {username}")
        return False, result
    
    username = result
    password = sanitize_input(password)
    
    if df_students.empty:
        return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    
    if student.empty:
        logger.warning(f"محاولة دخول بـ username غير موجود: {username}")
        return False, "❌ اسم المستخدم غير موجود"
    
    if student.iloc[0]["كلمة السر"].strip() != password:
        logger.warning(f"محاولة دخول بكلمة سر خاطئة لـ: {username}")
        return False, "❌ كلمة السر غير صحيحة"
    
    logger.info(f"تسجيل دخول ناجح: {username}")
    return True, student.iloc[0]

def verify_students_batch(students_data, df_students):
    """التحقق من بيانات عدة طلاب دفعة واحدة"""
    verified_students = []
    
    for username, password in students_data:
        if not username:
            continue
            
        valid, student = verify_student(username, password, df_students)
        if not valid:
            return False, student
        verified_students.append(student)
    
    return True, verified_students

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    """التحقق من كلمة سر الأستاذ"""
    valid, result = validate_note_number(note_number)
    if not valid:
        return False, None, result
    
    note_number = result
    prof_password = sanitize_input(prof_password)
    
    if df_memos.empty or df_prof_memos.empty:
        return False, None, "❌ خطأ في تحميل البيانات"
    
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    
    if memo_row.empty:
        logger.warning(f"محاولة تسجيل برقم مذكرة غير موجود: {note_number}")
        return False, None, "❌ رقم المذكرة غير موجود"
    
    memo_row = memo_row.iloc[0]
    
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم":
        logger.warning(f"محاولة تسجيل مذكرة مسجلة مسبقاً: {note_number}")
        return False, None, "❌ هذه المذكرة مسجلة مسبقاً لطالب آخر"
    
    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)
    ]
    
    if prof_row.empty:
        logger.warning(f"كلمة سر مشرف خاطئة للمذكرة: {note_number}")
        return False, None, "❌ كلمة سر المشرف غير صحيحة أو غير مخصصة لهذه المذكرة"
    
    if str(prof_row.iloc[0].get("تم التسجيل", "")).strip() == "نعم":
        logger.warning(f"محاولة استخدام كلمة سر مستخدمة مسبقاً للمذكرة: {note_number}")
        return False, None, "❌ هذه كلمة السر تم استعمالها مسبقًا"
    
    logger.info(f"تحقق ناجح من كلمة سر المشرف للمذكرة: {note_number}")
    return True, prof_row.iloc[0], None

# ---------------- تحديث المذكرات ----------------
def update_registration(note_number, student1, student2=None):
    """تحديث تسجيل المذكرة في جميع الجداول"""
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()

        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        prof_row_idx = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
            (df_prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
        ].index[0] + 2

        col_names = df_prof_memos.columns.tolist()
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}",
             "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}",
             "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}",
             "values": [[note_number]]}
        ]
        
        if student2 is not None:
            updates.append({
                "range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}",
                "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]
            })
        
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=PROF_MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        
        logger.info(f"تم تحديث شيت الأساتذة للمذكرة: {note_number}")

        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}",
             "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}",
             "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}",
             "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
        ]
        
        if student2 is not None:
            updates2.append({
                "range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}",
                "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]
            })
        
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates2}
        ).execute()
        
        logger.info(f"تم تحديث شيت المذكرات للمذكرة: {note_number}")

        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[note_number]]}
        ).execute()
        
        logger.info(f"تم تحديث بيانات الطالب الأول: {student1['اسم المستخدم']}")

        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()
            
            logger.info(f"تم تحديث بيانات الطالب الثاني: {student2['اسم المستخدم']}")

        time.sleep(2)
        clear_cache_and_reload()
        time.sleep(1)
        
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[
            df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()
        ].iloc[0]
        
        if student2 is not None:
            st.session_state.student2 = df_students_updated[
                df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()
            ].iloc[0]
        
        logger.info(f"✅ تم تسجيل المذكرة {note_number} بنجاح")
        
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        prof_name = memo_data["الأستاذ"].strip()
        
        prof_memo_data = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name)
        ].iloc[0]
        
        prof_email = str(prof_memo_data.get("الإيميل", "")).strip()
        
        if prof_email and "@" in prof_email:
            email_sent, email_msg = send_email_to_professor(
                prof_email, 
                prof_name, 
                memo_data, 
                student1, 
                student2
            )
            
            if email_sent:
                logger.info(f"📧 {email_msg}")
            else:
                logger.warning(f"⚠️ {email_msg}")
        else:
            logger.warning(f"⚠️ لا يوجد إيميل صالح للأستاذ {prof_name}")
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
        
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ---------------- Session State ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.memo_type = "فردية"
    st.session_state.mode = "register"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False

def logout():
    """تسجيل الخروج"""
    username1 = 'unknown'
    username2 = None
    
    if st.session_state.student1 is not None:
        username1 = st.session_state.student1.get('اسم المستخدم', 'unknown')
    
    if st.session_state.student2 is not None:
        username2 = st.session_state.student2.get('اسم المستخدم', 'unknown')
    
    if username2:
        logger.info(f"تسجيل خروج: {username1} و {username2}")
    else:
        logger.info(f"تسجيل خروج: {username1}")
    
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.mode = "register"
    st.session_state.note_number = ""
    st.session_state.prof_password = ""
    st.session_state.show_confirmation = False
    st.rerun()

# تحميل البيانات
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()

# التحقق من تحميل البيانات
if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً أو الاتصال بالدعم الفني.")
    st.stop()

# ---------------- واجهة الدخول ----------------
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("<h5 style='text-align:center;'>جامعة محمد البشير الإبراهيمي</h5>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align:center;'>كلية الحقوق والعلوم السياسية</h6>", unsafe_allow_html=True)
st.markdown("""
    <div style="text-align:center; margin:20px 0;">
        <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="100">
    </div>
""", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#FFD700;'>منصة تسجيل مذكرة الماستر</h4>", unsafe_allow_html=True)

# ---------------- عملية تسجيل الدخول ----------------
if not st.session_state.logged_in:
    st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])
    username1 = st.text_input("اسم المستخدم الطالب الأول", max_chars=50)
    password1 = st.text_input("كلمة السر الطالب الأول", type="password", max_chars=50)
    username2 = password2 = None
    
    if st.session_state.memo_type == "ثنائية":
        username2 = st.text_input("اسم المستخدم الطالب الثاني", max_chars=50)
        password2 = st.text_input("كلمة السر الطالب الثاني", type="password", max_chars=50)

    if st.button("تسجيل الدخول"):
        if st.session_state.memo_type == "ثنائية":
            if not username2 or not password2:
                st.markdown('<div class="error-msg">⚠️ يرجى إدخال بيانات الطالب الثاني كاملة</div>', unsafe_allow_html=True)
                logger.warning("محاولة تسجيل ثنائي بدون بيانات الطالب الثاني")
                st.stop()
            
            if username1.strip().lower() == username2.strip().lower():
                st.markdown('<div class="error-msg">❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!</div>', unsafe_allow_html=True)
                logger.warning(f"محاولة تسجيل ثنائي بنفس اسم المستخدم: {username1}")
                st.stop()
        
        students_data = [(username1, password1)]
        if st.session_state.memo_type == "ثنائية" and username2:
            students_data.append((username2, password2))
        
        valid, result = verify_students_batch(students_data, df_students)
        
        if not valid:
            st.markdown(f'<div class="error-msg">{result}</div>', unsafe_allow_html=True)
        else:
            verified_students = result
            st.session_state.student1 = verified_students[0]
            st.session_state.student2 = verified_students[1] if len(verified_students) > 1 else None
            
            if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
                s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                s1_specialty = str(st.session_state.student1.get('التخصص', '')).strip()
                s2_specialty = str(st.session_state.student2.get('التخصص', '')).strip()
                
                if s1_specialty != s2_specialty:
                    st.markdown('<div class="error-msg">❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل ثنائي بتخصصات مختلفة: {username1} ({s1_specialty}) و {username2} ({s2_specialty})")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if (s1_note and not s2_note) or (not s1_note and s2_note):
                    registered_student = None
                    if s1_note:
                        registered_student = f"{st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}"
                    else:
                        registered_student = f"{st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}"
                    
                    st.markdown(f'<div class="error-msg">❌ أحد الطالبين مسجل مسبقاً: {registered_student}<br>لا يمكن المتابعة</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل ثنائي مع طالب مسجل: {registered_student}")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if s1_note and s2_note and s1_note != s2_note:
                    st.markdown(f'<div class="error-msg">❌ الطالبان مسجلان في مذكرتين مختلفتين<br>الطالب الأول في المذكرة: {s1_note}<br>الطالب الثاني في المذكرة: {s2_note}<br>لا يمكن المتابعة</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة دخول ثنائي بمذكرتين مختلفتين: {s1_note} و {s2_note}")
                    st.session_state.logged_in = False
                    st.session_state.student1 = None
                    st.session_state.student2 = None
                    st.stop()
                
                if s1_note and s2_note and s1_note == s2_note:
                    st.session_state.mode = "view"
                    logger.info(f"دخول ثنائي لمذكرة مسجلة: {username1} و {username2}")
                    st.session_state.logged_in = True
                    st.rerun()
            
            if st.session_state.memo_type == "فردية":
                fardiya_value = str(st.session_state.student1.get('فردية', '')).strip()
                if fardiya_value not in ["1", "نعم"]:
                    st.markdown('<div class="error-msg">❌ لا يمكنك تسجيل مذكرة فردية. يرجى الاتصال بمسؤول الميدان</div>', unsafe_allow_html=True)
                    logger.warning(f"محاولة تسجيل فردي ممنوع: {username1} (قيمة فردية: {fardiya_value})")
                    st.stop()
            
            note_number = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
            
            if note_number:
                st.session_state.mode = "view"
                logger.info(f"الطالب مسجل مسبقاً: {username1}")
            else:
                st.session_state.mode = "register"
            
            st.session_state.logged_in = True
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- فضاء الطالب ----------------
if st.session_state.logged_in:
    s1 = st.session_state.student1
    s2 = st.session_state.student2
    
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h2 style='text-align:center;'>📘 فضاء الطالب</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_btn"):
            logout()
    
    st.markdown(f"👤 الطالب الأول: **{s1['اللقب']} {s1['الإسم']}**")
    st.markdown(f"🎓 التخصص: **{s1['التخصص']}**")
    
    if s2 is not None:
        st.markdown(f"👤 الطالب الثاني: **{s2['اللقب']} {s2['الإسم']}**")

    if st.session_state.mode == "view":
        time.sleep(0.5)
        
        df_memos_fresh = load_memos()
        
        note_number = str(s1.get('رقم المذكرة', '')).strip()
        memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number]
        
        if not memo_info.empty:
            memo_info = memo_info.iloc[0]
            st.markdown('<div class="success-msg">', unsafe_allow_html=True)
            st.markdown(f"### ✅ أنت مسجل في المذكرة التالية:")
            st.markdown(f"**📄 رقم المذكرة:** {memo_info['رقم المذكرة']}")
            st.markdown(f"**📑 عنوان المذكرة:** {memo_info['عنوان المذكرة']}")
            st.markdown(f"**👨‍🏫 الأستاذ المشرف:** {memo_info['الأستاذ']}")
            st.markdown(f"**🎯 التخصص:** {memo_info['التخصص']}")
            st.markdown(f"**🕒 تاريخ التسجيل:** {memo_info.get('تاريخ التسجيل','')}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-msg">⚠️ لم يتم العثور على معلومات المذكرة. يرجى تحديث الصفحة.</div>', unsafe_allow_html=True)
            if st.button("🔄 تحديث الصفحة"):
                clear_cache_and_reload()
                time.sleep(1)
                st.rerun()
        
        st.markdown('<div class="info-msg">', unsafe_allow_html=True)
        st.markdown("ℹ️ **ملاحظة:** لا يمكن تسجيل مذكرة أخرى. إذا كان هناك خطأ، يرجى الاتصال بالإدارة.")
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.mode == "register":
        st.markdown('<div class="info-msg">', unsafe_allow_html=True)
        st.markdown("### 📝 تسجيل مذكرة جديدة")
        st.markdown("⚠️ اختر الأستاذ المشرف والمذكرة التي ترغب في تسجيلها")
        st.markdown('</div>', unsafe_allow_html=True)
        
        all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
        selected_prof = st.selectbox("🧑‍🏫 اختر الأستاذ المشرف:", [""] + all_profs)
        
        if selected_prof:
            student_specialty = s1["التخصص"]
            available_memos_df = df_memos[
                (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
            ][["رقم المذكرة", "عنوان المذكرة"]]
            
            if not available_memos_df.empty:
                st.markdown(f'<p style="color:#4CAF50; font-weight:bold;">✅ المذكرات المتاحة لتخصصك ({student_specialty}):</p>', unsafe_allow_html=True)
                
                for idx, row in available_memos_df.iterrows():
                    st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
            else:
                st.markdown('<div class="error-msg">❌ لا توجد مذكرات متاحة لهذا الأستاذ مع تخصصك.</div>', unsafe_allow_html=True)

        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.note_number = st.text_input(
                "📄 رقم المذكرة", 
                value=st.session_state.note_number,
                max_chars=20
            )
        with col2:
            st.session_state.prof_password = st.text_input(
                "🔑 كلمة سر المشرف", 
                type="password",
                max_chars=50
            )

        if not st.session_state.show_confirmation:
            if st.button("📝 المتابعة للتأكيد", type="primary", use_container_width=True):
                if not st.session_state.note_number or not st.session_state.prof_password:
                    st.markdown('<div class="error-msg">⚠️ يرجى إدخال رقم المذكرة وكلمة سر المشرف</div>', unsafe_allow_html=True)
                else:
                    st.session_state.show_confirmation = True
                    st.rerun()
        else:
            st.markdown('<div class="info-msg">', unsafe_allow_html=True)
            st.markdown("### ⚠️ تأكيد التسجيل")
            st.markdown(f"**رقم المذكرة:** {st.session_state.note_number}")
            st.markdown(f"**الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
            if s2 is not None:
                st.markdown(f"**الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
            st.markdown("**⚠️ تنبيه:** بعد التأكيد، لن تتمكن من تغيير المذكرة!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ تأكيد نهائي", type="primary", use_container_width=True):
                    valid_memo, prof_row, error_msg = verify_professor_password(
                        st.session_state.note_number, 
                        st.session_state.prof_password, 
                        df_memos, 
                        df_prof_memos
                    )
                    
                    if not valid_memo:
                        st.markdown(f'<div class="error-msg">{error_msg}</div>', unsafe_allow_html=True)
                        st.session_state.show_confirmation = False
                    else:
                        with st.spinner('⏳ جاري تسجيل المذكرة...'):
                            success, message = update_registration(
                                st.session_state.note_number, 
                                s1, 
                                s2
                            )
                        
                        if success:
                            st.markdown(f'<div class="success-msg">{message}</div>', unsafe_allow_html=True)
                            st.balloons()
                            
                            clear_cache_and_reload()
                            st.session_state.mode = "view"
                            st.session_state.show_confirmation = False
                            
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{message}</div>', unsafe_allow_html=True)
                            st.session_state.show_confirmation = False
            
            with col2:
                if st.button("❌ إلغاء", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#888; font-size:12px; padding:20px;'>
        <p>© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>
        <p>للدعم الفني، يرجى الاتصال بالإدارة</p>
    </div>
""", unsafe_allow_html=True)