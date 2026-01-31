import streamlit as st
from datetime import datetime, time, date
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import textwrap

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ========================
# إعداد الموعد النهائي
# ========================
# يرجى تعديل السنة (2025) إذا كان الموعد في سنة أخرى
REGISTRATION_DEADLINE = datetime(2024
 , 1, 28, 23, 59)

# ---------------- CSS (تصميم زرقاء بلا حدود ومثبت) ----------------
st.markdown("""
<!-- استدعاء خط احترافي -->
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">

<style>
* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right;
}

/* الخلفية الأساسية */
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }

/* النصوص والعناوين */
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #F8FAFC; }
label, p, span { color: #E2E8F0; }
.stTextInput label, .stSelectbox label { color: #F8FAFC !important; font-weight: 600; }

/* الأزرار */
.stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
    background-color: #2F6F7E !important; color: #ffffff !important;
    font-size: 16px; font-weight: 600; padding: 14px 32px;
    border: none !important; border-radius: 12px !important;
    cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease; width: 100%;
    text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
}
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

/* البطاقات الاحترافية */
.card {
    background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(255,255,255, 0.08);
    border-radius: 20px; padding: 30px; margin-bottom: 20px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
}

/* بطاقات الإحصائيات */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
.kpi-card {
    background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
    text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
}
.kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
.kpi-label { font-size: 1.2rem; color: #94A3B8; font-weight: 600; margin-top: 10px; }

/* التنبيهات */
.alert-card {
    background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
    border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
    box-shadow: 0 10px 20px -5px rgba(139, 69, 19, 0.4); text-align: center; font-weight: bold;
}

/* شريط التقدم */
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 4px 6px rgba(0, 0, 0, 0.3); }
.progress-bar {
    height: 24px; border-radius: 99px;
    background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
    box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}

/* الجداول */
.stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,white, 0.1); background: #1E293B; }
.stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

/* التبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; }
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #94A3B8; font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
.stTabs [aria-selected="true"] {
    background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
}

.btn-select {
    margin-top: 10px; background-color: transparent !important;
    border: 1px dashed #2F6F7E !important; color: #94A3B8 !important; padding: 8px !important; font-size: 14px !important;
}
.btn-select:hover { background-color: #2F6F7E !important; color: white !important; }

/* =======================
   تصميم العرض الكامل (Fixed Layout)
   ======================= */
.full-view-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 40px;
    background: rgba(15,23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    box-shadow: 0 0 40px rgba(0,0,0,0.6);
    overflow: hidden;
}

.students-grid {
    display: flex;
    justify-content: center;
    gap: 40px;
    flex-wrap: wrap;
    margin-top: 20px;
    margin-bottom: 30px;
}

.student-card {
    flex: 1;
    max-width: 450px;
    min-width: 300px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 25px;
    text-align: center;
    transition: all 0.3s ease;
}
.student-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: #2F6F7E;
}

.memo-badge {
    display: inline-block; background: rgba(47, 111, 126, 0.2);
    color: #FFD700; padding: 6px 16px; border-radius: 20px;
    font-size: 1rem; margin-bottom: 10px; font-weight: 600;
}
.memo-id { font-size: 3rem; font-weight: 900; color: #2F6F7E; margin: 0; line-height: 1; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets: تأكد من ملف Secrets.")
    st.stop()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:U1000" # تم توسيع النطاق ليشمل عمود الجلسة
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "oevruyiztgikwzah"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- دوال مساعدة ----------------
def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result

def sanitize_input(text):
    if not text: return ""
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`']
    cleaned = str(text).strip()
    for char in dangerous_chars: cleaned = cleaned.replace(char, '')
    return cleaned

def validate_username(username):
    username = sanitize_input(username)
    if not username: return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number: return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20: return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

def get_email_smart(row):
    """
    دالة محسنة جداً لاستخراج الإيميل:
    1. تبحث في نطاق أوسع حول العمود K (من 9 إلى 12).
    2. تقبل الأرقام التي تحتوي على نقاط (.0).
    3. تبحث بالاسم بعد تنظيف المسافات.
    """
    # 1. تحويل الصف إلى قائمة
    values_list = row.tolist()
    
    # 2. البحث العشوائي الذكي حول العمود K (الفهرس 10) في حال كان هناك إزاحة بسيطة في الأعمدة
    # سنبحث في الأعمدة 9, 10, 11, 12 (J, K, L, M)
    for i in range(9, 13):
        if i < len(values_list):
            val = str(values_list[i]).strip()
            # نتحقق من وجود @ وأن القيمة ليست nan أو فارغة
            if "@" in val and val != "nan":
                return val

    # 3. محاولة البحث بالاسم مع تنظيف أسماء الأعمدة
    # نقوم بعمل loop على أسماء الأعمدة وننظفها قبل المقارنة
    for col in row.index:
        clean_col_name = str(col).strip()
        if clean_col_name in ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]:
            val = str(row[col]).strip()
            if "@" in val and val != "nan":
                return val
                
    return ""

def get_student_info_from_memo(memo_row, df_students):
    student1_name = str(memo_row.get("الطالب الأول", "")).strip()
    student2_name = str(memo_row.get("الطالب الثاني", "")).strip()
   
    s1_email = s2_email = s1_reg_display = s2_reg_display = ""
    
    # استدعاء الدالة المساعدة
    email_fetcher = get_email_smart

    # --- قراءة رقم التسجيل من الأعمدة S و T ---
    try:
        memo_list = memo_row.tolist()
        
        # قراءة القيم الخام وتنظيفها من النقطة إن وجدت
        raw_reg1 = str(memo_list[18]).strip() if len(memo_list) > 18 else ""
        raw_reg2 = str(memo_list[19]).strip() if len(memo_list) > 19 else ""
        
        # تنظيف النقطة .0 إن وجدت (لضمان التطابق)
        reg1 = raw_reg1.replace('.0', '')
        reg2 = raw_reg2.replace('.0', '')
        
    except:
        # الاحتياطي
        reg1 = str(memo_row.get("رقم تسجيل الطالب 1", "")).replace('.0', '').strip()
        reg2 = str(memo_row.get("رقم تسجيل الطالب 2", "")).replace('.0', '').strip()

    # --- جلب بيانات الطالب الأول ---
    if reg1:
        # محاولة البحث: ننظف رقم التسجيل في شيت الطلاب أيضاً من النقطة .0
        df_students['رقم التسجيل'] = df_students['رقم التسجيل'].astype(str).str.replace('.0', '').str.strip()
        
        s_data = df_students[df_students["رقم التسجيل"] == reg1]
        if not s_data.empty:
            s1_email = email_fetcher(s_data.iloc[0])
            s1_reg_display = reg1

    # --- جلب بيانات الطالب الثاني ---
    if student2_name and reg2:
        s_data = df_students[df_students["رقم التسجيل"] == reg2]
        if not s_data.empty:
            s2_email = email_fetcher(s_data.iloc[0])
            s2_reg_display = reg2

    return {
        "s1_name": student1_name, "s1_email": s1_email, "s1_reg": s1_reg_display,
        "s2_name": student2_name, "s2_email": s2_email, "s2_reg": s2_reg_display
    }

@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # --- تعديل هام: تنظيف أسماء الأعمدة من المسافات الزائدة ---
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلاب: {str(e)}")
        return pd.DataFrame()
     
@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات المذكرات: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات مذكرات الأساتذة: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values', [])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        logger.error(f"خطأ في تحميل بيانات الطلبات: {str(e)}")
        return pd.DataFrame()

def clear_cache_and_reload():
    st.cache_data.clear()
    logger.info("تم مسح السجلات")

def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        students_with_memo = df_s[df_s["رقم المذكرة"].notna() & (df_s["رقم المذكرة"] != "")]
        for index, row in df_m.iterrows():
            memo_num = str(row.get("رقم المذكرة", "")).strip()
            if not memo_num: continue
            matched_students = students_with_memo[students_with_memo["رقم المذكرة"].astype(str).str.strip() == memo_num]
            if matched_students.empty: continue
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            reg_s1 = ""; reg_s2 = ""
            for _, s_row in matched_students.iterrows():
                lname = s_row.get('لقب', s_row.get('اللقب', ''))
                fname = s_row.get('إسم', s_row.get('إسم', ''))
                full_name = f"{lname} {fname}".strip()
                if full_name == s1_name: reg_s1 = str(s_row.get("رقم التسجيل", ""))
                elif s2_name and full_name == s2_name: reg_s2 = str(s_row.get("رقم التسجيل", ""))
            if not reg_s1 and len(matched_students) > 0: reg_s1 = str(matched_students.iloc[0].get("رقم التسجيل", ""))
            row_idx = index + 2
            if reg_s1: updates.append({"range": f"Feuille 1!S{row_idx}", "values": [[reg_s1]]})
            if reg_s2: updates.append({"range": f"Feuille 1!T{row_idx}", "values": [[reg_s2]]})
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية بنجاح."
        else: return False, "ℹ️ جميع البيانات محدثة أو لا توجد تطابقات."
    except Exception as e:
        logger.error(f"Migration Error: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text, status="قيد المراجعة"):
    """
    حفظ الطلب في جدول الطلبات
    الأعمدة حسب الشيت: رقم الطلب, الوقت, النوع, الحالة, الأستاذ, رقم المذكرة, ...
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # ترك "رقم الطلب" فارغاً ليتم توليده تلقائياً أو يدوياً
        new_row = ["", timestamp, req_type, status, prof_name, memo_id, "", "", details_text, "", ""]
        
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        
        # إرسال إيميل للإدارة
        request_titles = {
            "تغيير عنوان المذكرة": "طلب تغيير عنوان مذكرة",
            "حذف طالب": "طلب حذف طالب من مذكرة ثنائية",
            "إضافة طالب": "طلب إضافة طالب لمذكرة فردية",
            "تنازل": "طلب تنازل عن الإشراف",
            "جلسة إشراف": "تنبيه: جلسة إشراف مجدولة"
        }
        subject = f"{request_titles.get(req_type, 'طلب جديد')} - {prof_name}"
        
        email_body = f"<html dir='rtl'><body style='font-family:sans-serif; padding:20px;'><div style='background:#f4f4f4; padding:30px; border-radius:10px; max-width:600px; margin:auto; color:#333;'><h2 style='background:#8B4513; color:white; padding:20px; border-radius:8px; text-align:center;'>{subject}</h2><p><strong>من:</strong> {prof_name}</p><p><strong>رقم/نوع:</strong> {memo_id}</p><div style='background:#fff8dc; padding:15px; border-right:4px solid #8B4513; margin:15px 0; border-radius: 8px;'><h3>التفاصيل:</h3><p>{details_text}</p></div></div></body></html>"
        
        msg = MIMEMultipart('alternative')
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, ADMIN_EMAIL, subject
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
            
        return True, "✅ تم تسجيل الطلب في النظام وإرسال الإيميل للإدارة"
    except Exception as e:
        logger.error(f"Request Error: {str(e)}")
        return False, f"❌ حدث خطأ أثناء تسجيل الطلب: {str(e)}"

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]
        if memo_row.empty: return False, "❌ لم يتم العثور على المذكرة"
        row_idx = memo_row.index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{row_idx}",
            valueInputOption="USER_ENTERED", body={"values": [[str(progress_value)]]}
        ).execute()
        clear_cache_and_reload()
        logger.info(f"تم تحديث نسبة التقدم للمذكرة {memo_number} إلى {progress_value}%")
        return True, "✅ تم تحديث نسبة التقدم بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث نسبة التقدم: {str(e)}")
        return False, f"❌ خطأ: {str(e)}"

# ---------------- دوال الجلسات والطلبات الجديدة ----------------

def format_datetime_ar(date_obj, time_str):
    """تنسيق التاريخ والوقت للعرض العربي"""
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    day_name = days_ar[date_obj.weekday()]
    date_str = date_obj.strftime('%Y-%m-%d')
    return f"{day_name} {date_str} الساعة {time_str}"

def get_students_of_professor(prof_name, df_memos):
    """جلب قائمة بالطلاب المسجلين (السيناريو أ) الذين يشرف عليهم الأستاذ"""
    prof_memos = df_memos[
        (df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()) & 
        (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")
    ]
    
    students_data = []
    for _, memo in prof_memos.iterrows():
        s1_name = str(memo.get("الطالب الأول", "")).strip()
        s1_reg = str(memo.get("رقم تسجيل الطالب 1", memo.get("رقم التسجيل 1", ""))).strip()
        if s1_name and s1_name != "--" and s1_reg:
            students_data.append({"name": s1_name, "reg": s1_reg, "memo": memo.get("رقم المذكرة")})
            
        s2_name = str(memo.get("الطالب الثاني", "")).strip()
        s2_reg = str(memo.get("رقم تسجيل الطالب 2", memo.get("رقم التسجيل 2", ""))).strip()
        if s2_name and s2_name != "--" and s2_reg:
            students_data.append({"name": s2_name, "reg": s2_reg, "memo": memo.get("رقم المذكرة")})
            
    return students_data

def update_session_date_in_sheets(prof_name, date_str):
    """تحديث عمود 'موعد الجلسة القادمة' في جميع مذكرات الأستاذ"""
    try:
        df_memos = load_memos()
        masks = (df_memos["الأستاذ"].astype(str).str.strip() == prof_name) & \
                (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")
        target_indices = df_memos[masks].index
        
        if target_indices.empty:
            return True, "لا توجد مذكرات لتحديثها"
        
        updates = []
        col_names = df_memos.columns.tolist()
        target_col_name = "موعد الجلسة القادمة"
        
        if target_col_name in col_names:
            col_idx = col_names.index(target_col_name) + 1
            col_letter_str = col_letter(col_idx)
        else:
            # افتراضياً العمود الأخير إذا لم يتم العثور عليه
            col_idx = len(col_names)
            col_letter_str = col_letter(col_idx)
            
        for idx in target_indices:
            row_num = idx + 2
            updates.append({
                "range": f"Feuille 1!{col_letter_str}{row_num}",
                "values": [[date_str]]
            })
            
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID, body=body
        ).execute()
        
        return True, "تم تحديث التواريخ بنجاح"
    except Exception as e:
        logger.error(f"Update Session Error: {e}")
        return False, str(e)

def send_session_emails(students_data, session_info, prof_name):
    """
    إرسال إيميل للإدارة (للنشر) ونسخة مخفية لجميع الطلاب المشمولين
    """
    try:
        df_students = load_students()
        student_emails = []
        
        for s in students_data:
            s_row = df_students[df_students["رقم التسجيل"].astype(str).str.strip() == s['reg']]
            if not s_row.empty:
                email = ""
                possible_cols = ["البريد المهني", "البريد الإلكتروني", "email", "Email"]
                for col in possible_cols:
                    if col in s_row.columns:
                        val = str(s_row.iloc[0][col]).strip()
                        if val and val != "nan" and "@" in val:
                            email = val
                            break
                
                if email:
                    student_emails.append(email)

        subject = f"🔔 تنبيه هام: جلسة إشراف - {prof_name}"
        
        students_list_html = "<ul>"
        for i, s in enumerate(students_data):
            if i < 10: 
                students_list_html += f"<li>{s['name']}</li>"
            else:
                students_list_html += f"<li>... و {len(students_data) - 10} طالب آخر</li>"
                break
        students_list_html += "</ul>"

        email_body = f"""
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; border-top: 5px solid #256D85; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .highlight {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; font-size: 1.1em; }}
                .footer {{ text-align: center; color: #777; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="color: #256D85; margin: 0;">📅 جدولة جلسة إشراف</h2>
                </div>
                
                <p>السلام عليكم ورحمة الله،</p>
                <p>يُعلن الأستاذ(ة) <b>{prof_name}</b> عن تنظيم جلسة إشراف للمذكرات.</p>
                
                <div class="highlight">
                    <strong>📆 الموعد:</strong> {session_info}
                </div>

                <p>تم توجيه هذا الإشعار إلى الطلبة المسجلين تحت إشراف الأستاذ:</p>
                {students_list_html}

                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p style="font-size: 0.9em; color: #555;">
                    <strong>للإدارة:</strong> يرجى نشر هذا الموعد في الفيسبوك وإعلام الطلبة غير الحاصلين على بريد إلكتروني.
                </p>
            </div>
            <div class="footer">
                جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject
        
        if student_emails:
            msg['Bcc'] = ", ".join(student_emails)
            
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"✅ Session email sent to Admin and {len(student_emails)} students.")
        return True, "تم الإرسال"
        
    except Exception as e:
        logger.error(f"Error sending session emails: {e}")
        return False, str(e)

# ---------------- دالة الإرسال للأستاذ ----------------
def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    """إرسال بريد إلكتروني للأستاذ (نسخة ذكية للتعامل مع اختلافات البيانات)"""
    try:
        df_prof_memos = load_prof_memos()
        
        prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_row.empty:
            clean_name = prof_name.strip().replace("الأستاذ", "").replace("د.", "").replace("أ.د", "").strip()
            if clean_name:
                prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.contains(clean_name, case=False, na=False)]
        
        if prof_row.empty:
            error_msg = f"فشل الإرسال: لم يتم العثور على البريد للأستاذ <b>{prof_name}</b>."
            logger.error(f"Email Error: Professor {prof_name} not found.")
            return False, error_msg

        prof_data = prof_row.iloc[0]
        prof_email = ""
        possible_email_cols = ["البريد الإلكتروني", "الإيميل", "email", "Email"]
        for col in possible_email_cols:
            if col in prof_data.index:
                val = str(prof_data[col]).strip()
                if val and val != "nan":
                    prof_email = val
                    break
        
        if "@" not in prof_email:
            error_msg = f"فشل الإرسال: الأستاذ <b>{prof_name}</b> موجود، ولكن البريد الإلكتروني فارغ."
            logger.error(f"Email Error: Invalid email for Prof {prof_name}: {prof_email}")
            return False, error_msg

        total_memos = len(prof_row)
        registered_memos = len(prof_row[prof_row["تم التسجيل"].astype(str).str.strip() == "نعم"])
        
        s1_lname = student1.get('لقب', student1.get('اللقب', ''))
        s1_fname = student1.get('إسم', student1.get('إسم', ''))
        student2_info = ""
        
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', ''))
            s2_fname = student2.get('إسم', student2.get('إسم', ''))
            student2_info = f"\n👤 **الطالب الثاني:** {s2_lname} {s2_fname}"
        
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
            <p>تحية طيبة، الأستاذ(ة) <span class="highlight">{prof_name}</span>،</p>
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
                    <li>⏳ <strong>المذكرات المتبقية:</strong> {total_memos - registered_memos}</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px; color: #666;">للاستفسار، يرجى التواصل مع الإدارة.</p>
        </div>
        <div class="footer">
            <p>© 2026 جامعة محمد البشير الإبراهيمي</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة جديدة - رقم {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email sent to professor {prof_name}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False, f"خطأ تقني أثناء الإرسال: {str(e)}"

# ---------------- دوال التحقق ----------------
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username]
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    if student.iloc[0]["كلمة السر"].strip() != password: return False, "❌ كلمة السر غير صحيحة"
    return True, student.iloc[0].to_dict()

def verify_students_batch(students_data, df_students):
    verified_students = []
    for username, password in students_data:
        if not username: continue
        valid, student = verify_student(username, password, df_students)
        if not valid: return False, student
        verified_students.append(student)
    return True, verified_students

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty: return False, "❌ خطأ في تحميل بيانات الأساتذة"
    required_cols = ["إسم المستخدم", "كلمة المرور"]
    if any(col not in df_prof_memos.columns for col in required_cols): return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    prof = df_prof_memos[(df_prof_memos["إسم المستخدم"].astype(str).str.strip() == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)]
    if prof.empty: return False, "❌ اسم المستخدم أو كلمة السر غير صحيحة"
    return True, prof.iloc[0].to_dict()

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password: return True, username
    return False, "❌ بيانات الإدارة غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid: return False, None, result
    note_number = result
    prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty: return False, None, "❌ خطأ في تحميل البيانات"
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0].to_dict(), None

def update_registration(note_number, student1, student2=None):
    try:
        df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        # --- تحديث البيانات في الجداول ---
        prof_row_idx = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)].index[0] + 2
        col_names = df_prof_memos.columns.tolist()
        s1_lname = student1.get('لقب', student1.get('اللقب', '')); s1_fname = student1.get('إسم', student1.get('إسم', ''))
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        
        if student2 is not None:
            s2_lname = student2.get('لقب', student2.get('اللقب', '')); s2_fname = student2.get('إسم', student2.get('إسم', ''))
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()
        
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        reg1 = str(student1.get('رقم التسجيل', '')); reg2 = str(student2.get('رقم التسجيل', '')) if student2 else ""
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!S{memo_row_idx}", "values": [[reg1]]}
        ]
        
        if 'كلمة سر التسجيل' in memo_cols: updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[reg2]]})
        
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()
        
        students_cols = df_students.columns.tolist()
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        time.sleep(2); clear_cache_and_reload(); time.sleep(1)
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].iloc[0].to_dict()
        if student2 is not None: st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].iloc[0].to_dict()
        
        # --- إرسال الإيميل (مع عرض الأخطاء) ---
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
        email_sent, email_msg = send_email_to_professor(
            prof_name, 
            memo_data, 
            st.session_state.student1, 
            st.session_state.student2 if student2 else None
        )
        
        if not email_sent:
            st.error(f"⚠️ {email_msg}")
            st.warning("تم تسجيل المذكرة في النظام، ولكن لم يتم إرسال الإيميل للأستاذ.")
        else:
            st.success("📧 تم إرسال إشعار بالبريد الإلكتروني للأستاذ.")
            
        return True, "✅ تم تسجيل المذكرة بنجاح!"
        
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ---------------- Session State ----------------
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
    st.session_state.logged_in = False
    st.session_state.student1 = None; st.session_state.student2 = None; st.session_state.professor = None
    st.session_state.admin_user = None; st.session_state.memo_type = "فردية"; st.session_state.mode = "register"
    st.session_state.note_number = ""; st.session_state.prof_password = ""; st.session_state.show_confirmation = False
    st.session_state.selected_memo_id = None

def logout():
    for key in st.session_state.keys():
        if key not in ['user_type']: del st.session_state[key]
    st.session_state.update({'logged_in': False, 'student1': None, 'student2': None, 'professor': None, 'admin_user': None, 'mode': "register", 'note_number': "", 'prof_password': "", 'show_confirmation': False, 'user_type': None, 'selected_memo_id': None})
    st.rerun()

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ============================================================
# الصفحة الرئيسية
# ============================================================
if st.session_state.user_type is None:
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.2rem;'>جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 1rem;'>منصة تسجيل المذكرات</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>🎓 فضاء الطلبة</h3>", unsafe_allow_html=True)
        if st.button("دخول الطلبة", key="btn_student", use_container_width=True): st.session_state.user_type = "student"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>📚 فضاء الأساتذة</h3>", unsafe_allow_html=True)
        if st.button("دخول الأساتذة", key="btn_prof", use_container_width=True): st.session_state.user_type = "professor"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3>⚙️ فضاء الإدارة</h3>", unsafe_allow_html=True)
        if st.button("دخول الإدارة", key="btn_admin", use_container_width=True): st.session_state.user_type = "admin"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# فضاء الطلبة
# ============================================================
elif st.session_state.user_type == "student":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>فضاء الطلبة</h2>", unsafe_allow_html=True)
        st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
        with st.form("student_login_form"):
            username1 = st.text_input("اسم المستخدم الطالب الأول")
            password1 = st.text_input("كلمة السر الطالب الأول", type="password")
            username2 = password2 = None
            if st.session_state.memo_type == "ثنائية":
                st.markdown("---")
                username2 = st.text_input("اسم المستخدم الطالب الثاني")
                password2 = st.text_input("كلمة السر الطالب الثاني", type="password")
            submitted = st.form_submit_button("تسجيل الدخول")
            if submitted:
                if st.session_state.memo_type == "فردية":
                    if not username1 or not password1: st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة السر"); st.stop()
                if st.session_state.memo_type == "ثنائية":
                    if not username1 or not password1 or not username2 or not password2: st.error("⚠️ يرجى إدخال بيانات الطالبين كاملة"); st.stop()
                    if username1.strip().lower() == username2.strip().lower(): st.error("❌ لا يمكن أن يكون الطالب الأول والثاني نفس الشخص!"); st.stop()
                students_data = [(username1, password1)]
                if st.session_state.memo_type == "ثنائية" and username2: students_data.append((username2, password2))
                valid, result = verify_students_batch(students_data, df_students)
                if not valid: st.error(result)
                else:
                    verified_students = result
                    if not verified_students: st.error("حدث خطأ غير متوقع في التحقق من البيانات"); st.stop()
                    st.session_state.student1 = verified_students[0]
                    st.session_state.student2 = verified_students[1] if len(verified_students) > 1 else None
                    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
                        s1_note = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                        s2_note = str(st.session_state.student2.get('رقم المذكرة', '')).strip()
                        s1_spec = str(st.session_state.student1.get('التخصص', '')).strip()
                        s2_spec = str(st.session_state.student2.get('التخصص', '')).strip()
                        if s1_spec != s2_spec: st.error("❌ لا يمكن التسجيل الثنائي. الطالبان في تخصصين مختلفين"); st.session_state.logged_in=False; st.stop()
                        if (s1_note and not s2_note) or (not s1_note and s2_note): st.error("❌ أحد الطالبين مسجل مسبقاً"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note != s2_note: st.error(f"❌ الطالبان مسجلان في مذكرتين مختلفتين"); st.session_state.logged_in=False; st.stop()
                        if s1_note and s2_note and s1_note == s2_note: st.session_state.mode = "view"; st.session_state.logged_in = True; st.rerun()
                    if st.session_state.memo_type == "فردية":
                        fardiya_val = str(st.session_state.student1.get('فردية', '')).strip()
                        if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                    note_num = str(st.session_state.student1.get('رقم المذكرة', '')).strip()
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True; st.rerun()
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"): logout()
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1.get("لقب", s1.get("اللقب"))} {s1.get("الإسم", s1.get("إسم"))}</b></p><p>التخصص: <b>{s1.get("التخصص")}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2.get("لقب", s2.get("اللقب"))} {s2.get("الإسم", s2.get("إسم"))}</b></p></div>', unsafe_allow_html=True)

        tab_memo, tab_notify = st.tabs(["مذكرتي", "الإشعارات والطلبات"])
        with tab_memo:
            if st.session_state.mode == "view":
                df_memos_fresh = load_memos()
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo_info.empty:
                    memo_info = memo_info.iloc[0]
                    # عرض الموعد إذا وجد
                    session_date = memo_info.get("موعد الجلسة القادمة", "")
                    session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date else ""
                    
                    st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p><p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p>{session_html}</div>''', unsafe_allow_html=True)
            elif st.session_state.mode == "register":
                # --- التحقق من الموعد النهائي ---
                if datetime.now() > REGISTRATION_DEADLINE:
                    st.markdown("""
                    <div class='alert-card' style='text-align:center; padding:40px; border: 2px solid #EF4444; background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);'>
                        <h2 style='font-size:2.5rem; margin-bottom:20px;'>⛔ انتهت مهلة التسجيل</h2>
                        <p style='font-size:1.3rem; margin:20px 0; line-height:1.6;'>
                            تم إيقاف خاصية التسجيل
                        </p>
                        <div style='background: rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-top:20px;'>
                            <p style='font-size:1.2rem; color:#FFD700; margin:0; font-weight:bold;'>
                                ⚠️ يرجى الاتصال بمكتب فريق التكوين في الكلية يوم الأحد 01 فيفري  2025 
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # --- نموذج التسجيل الأصلي ---
                    st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                    all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                    selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                    if selected_prof:
                        student_specialty = s1.get("التخصص")
                        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                        reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                        if reg_count >= 4: st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                        else:
                            avail_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) & (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")][["رقم المذكرة", "عنوان المذكرة"]]
                           
                            if not avail_memos.empty:
                                st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                                for _, row in avail_memos.iterrows(): st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                            else:
                                st.error('لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك حالياً ❌')
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
                    with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")
                    if not st.session_state.show_confirmation:
                        if st.button("المتابعة للتأكيد"):
                            if not st.session_state.note_number or not st.session_state.prof_password: st.error("⚠️ يرجى إدخال البيانات")
                            else: st.session_state.show_confirmation = True; st.rerun()
                    else:
                        st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("تأكيد نهائي", type="primary"):
                                valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                                if not valid: st.error(err); st.session_state.show_confirmation = False
                                else:
                                    with st.spinner('⏳ جاري تسجيل...'):
                                        success, msg = update_registration(st.session_state.note_number, s1, s2)
                                    if success: st.success(msg); st.balloons(); clear_cache_and_reload(); st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
                                    else: st.error(msg); st.session_state.show_confirmation = False
                        with col2:
                            if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()
        
        with tab_notify:
            st.subheader("تنبيهات خاصة بك")
            my_memo_id = str(s1.get('رقم المذكرة', '')).strip()
            
            if my_memo_id:
                # 1. عرض جلسات الإشراف
                df_memos_fresh = load_memos()
                my_memo_row = df_memos_fresh[df_memos_fresh["رقم المذكرة"] == my_memo_id]
                
                if not my_memo_row.empty:
                    my_prof = str(my_memo_row.iloc[0]["الأستاذ"]).strip()
                    
                    # تصحيح: استخدام "النوع" بدلاً من "نوع الطلب"
                    base_filter = df_requests["النوع"] == "جلسة إشراف"
                    prof_filter = df_requests["الأستاذ"].astype(str).str.strip() == my_prof
                    prof_sessions = df_requests[base_filter & prof_filter]

                    if not prof_sessions.empty:
                        last_session = prof_sessions.iloc[-1]
                        # عرض التفاصيل من عمود المبررات
                        st.markdown(f"""
                        <div class='card' style='border-right: 4px solid #3B82F6; background: rgba(59, 130, 246, 0.1);'>
                            <h4>🔔 جلسة إشراف</h4>
                            <p>{last_session['المبررات']}</p>
                            <small style='color: #666;'>{last_session['الوقت']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                # 2. عرض الطلبات العادية
                my_reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == my_memo_id]

                if not my_reqs.empty:
                    for _, r in my_reqs.iterrows():
                        req_type = r['النوع']
                        details = str(r.get('العنوان الجديد', r.get('المبررات', ''))).strip()
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]: show_details = False
                        st.markdown(f"""<div class='card' style='border-right: 4px solid #F59E0B; padding: 20px;'><h4>{req_type}</h4><p>التاريخ: {r['الوقت']}</p><p>الحالة: <b>{r.get('الحالة', 'غير محدد')}</b></p>{'<p>التفاصيل: ' + details + '</p>' if show_details else '<p><i>التفاصيل مخفية</i></p>'}</div>""", unsafe_allow_html=True)
                
                if prof_sessions.empty and my_reqs.empty:
                    st.info("لا توجد إشعارات جديدة.")
            else: 
                st.info("يجب تسجيل مذكرة أولاً لتلقي الإشعارات.")

# ============================================================
# فضاء الأساتذة
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_prof"):
                st.session_state.user_type = None
                st.rerun()
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
       
        if st.session_state.selected_memo_id:
            memo_id = st.session_state.selected_memo_id
            current_memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == memo_id].iloc[0]
            student_info = get_student_info_from_memo(current_memo, df_students)
           
            col_back, _, _ = st.columns([1, 8, 1])
            with col_back:
                if st.button("⬅️ العودة للقائمة"): st.session_state.selected_memo_id = None; st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            progress_val = str(current_memo.get('نسبة التقدم', '0')).strip()
            try: prog_int = int(progress_val) if progress_val else 0
            except: prog_int = 0

            student_cards_html = f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الأول</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s1_name']}</p>
    <p style="font-size: 0.9rem; color: #94A3B8;">رقم التسجيل: {student_info['s1_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s1_email'] or 'غير متوفر'}
    </div>
</div>
"""
            if student_info['s2_name']:
                student_cards_html += f"""
<div class="student-card">
    <h4 style="color: #FFD700; margin-top: 0; font-size: 1.1rem;">الطالب الثاني</h4>
    <p style="font-size: 1.3rem; font-weight: bold; margin: 15px 0 5px 0; color: #fff;">{student_info['s2_name']}</p>
    <p style="font-size: 0.9rem; color: #C0C0C0;">رقم التسجيل: {student_info['s2_reg'] or '--'}</p>
    <div style="margin-top: 15px; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; color: #10B981; font-size: 0.9rem;">
        📧 {student_info['s2_email'] or 'غير متوفر'}
    </div>
</div>
"""
           
            student_cards_html += "</div>"

            full_memo_html = f"""<div class="full-view-container">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap;">
    <div>
        <p class="memo-badge">{current_memo['التخصص']}</p>
        <h1 class="memo-id">{current_memo['رقم المذكرة']}</h1>
    </div>
</div>
<div style="text-align: center; border-bottom: 2px solid #2F6F7E; padding-bottom: 20px; margin-bottom: 30px;">
    <h2 style="color: #F8FAFC; font-size: 1.8rem; margin: 0; line-height: 1.6;">{current_memo['عنوان المذكرة']}</h2>
</div>
<div class="students-grid">
    {student_cards_html}
</div>
<div style="margin-bottom: 40px; text-align: center;">
    <h3 style="color: #F8FAFC; margin-bottom: 15px;">نسبة الإنجاز الحالية</h3>
    <div class="progress-container" style="height: 40px; border-radius: 20px;">
        <div class="progress-bar" style="width: """ + str(prog_int) + """%; font-size: 1.2rem; font-weight: bold; line-height: 28px;">""" + str(prog_int) + """%</div>
    </div>
</div>
</div>
"""
           
            st.markdown(textwrap.dedent(full_memo_html), unsafe_allow_html=True)
            st.markdown("<div class='divider' style='border-top: 1px solid #334155; margin: 30px 0;'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>إدارة المذكرة</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
           
            with col1:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📊 تحديث نسبة التقدم")
                new_prog = st.selectbox("اختر المرحلة:", ["0%", "10% - ضبط المقدمة", "30% - الفصل الأول", "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"], key=f"prog_full_{memo_id}")
                if st.button("حفظ التحديث", key=f"save_full_{memo_id}", use_container_width=True):
                    mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                    s, m = update_progress(memo_id, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
           
            with col2:
                st.markdown("<div style='background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 10px;'>", unsafe_allow_html=True)
                st.subheader("📨 إرسال طلب للإدارة")
                req_op = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل عن الإشراف"], key=f"req_full_{memo_id}")
                details_to_save = ""
                validation_error = None
               
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_full_{memo_id}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_full_{memo_id}", use_container_width=True):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                elif req_op == "حذف طالب (ثنائية)":
                    if not student_info['s2_name']: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:")
                        st.write(f"1. {student_info['s1_name']}")
                        st.write(f"2. {student_info['s2_name']}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_full_{memo_id}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_full_{memo_id}")
                        if st.button("إرسال طلب الحذف", key=f"btn_del_full_{memo_id}", use_container_width=True):
                            if to_del and just: details_to_save = f"حذف: {to_del}. السبب: {just}"
                            else: validation_error = "اكمل البيانات"
                elif req_op == "إضافة طالب (فردية)":
                    if student_info['s2_name']: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        reg_to_add = st.text_input("رقم التسجيل:", key=f"add_full_{memo_id}")
                        if st.button("تحقق وإرسال", key=f"btn_add_full_{memo_id}", use_container_width=True):
                            target = df_students[df_students["رقم التسجيل"] == reg_to_add]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("التخصص") != current_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات (اختياري):", key=f"jus_add_full_{memo_id}")
                                details_to_save = f"إضافة الطالب المسجل: {reg_to_add}. ملاحظات: {just}"
                elif req_op == "تنازل عن الإشراف":
                    just = st.text_area("مبررات التنازل:", key=f"res_full_{memo_id}")
                    if st.button("إرسال طلب التنازل", key=f"btn_res_full_{memo_id}", use_container_width=True):
                        if just: details_to_save = f"التنازل عن الإشراف. المبررات: {just}"
                        else: validation_error = "الرجاء كتابة المبررات"

                if validation_error:
                    st.error(validation_error)
                elif details_to_save:
                    suc, msg = save_and_send_request(req_op, prof_name, memo_id, current_memo['عنوان المذكرة'], details_to_save)
                    if suc: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج"): logout()
           
            st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)
            prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            total = len(prof_memos)
            registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
            available = total - registered
            is_exhausted = registered >= 4

            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{registered}</div><div class="kpi-label">المذكرات المسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{available}</div><div class="kpi-label">المذكرات المتاحة</div></div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
           
            tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "جدولة جلسة إشراف", "كلمات السر", "المذكرات المتاحة"])
           
            with tab1:
                st.subheader("المذكرات المسجلة")
                registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
                if not registered_memos.empty:
                    cols = st.columns(2)
                    for i, (_, memo) in enumerate(registered_memos.iterrows()):
                        with cols[i % 2]:
                            progress_val = str(memo.get('نسبة التقدم', '0')).strip()
                            try: prog_int = int(progress_val) if progress_val else 0
                            except: prog_int = 0
                            s_info = get_student_info_from_memo(memo, df_students)
                            st.markdown(f'''<div class="card" style="border-right: 5px solid #10B981; padding-bottom: 10px;"><h4>{memo['رقم المذكرة']} - {memo['عنوان المذكرة']}</h4><p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p><p style="font-size:0.95em; margin-bottom: 5px;">{s_info['s1_name']}</p>{f"<p style='font-size:0.95em; margin-bottom: 15px;'>{s_info['s2_name']}</p>" if s_info['s2_name'] else ""}<div class="progress-container" style="margin: 10px 0;"><div class="progress-bar" style="width: {prog_int}%;"></div></div><p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p></div>''', unsafe_allow_html=True)
                            if st.button(f"👉 عرض المذكرة {memo['رقم المذكرة']}", key=f"open_{memo['رقم المذكرة']}", use_container_width=True):
                                st.session_state.selected_memo_id = memo['رقم المذكرة']; st.rerun()
                else: st.info("لا توجد مذكرات مسجلة حتى الآن.")

            with tab2:
                st.subheader("📅 جدولة جلسة إشراف")
                st.info("سيتم إرسال الإشعار لكل الطلبة المسجلين لديك في المذكرات.")
                
                with st.form("supervision_session_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        selected_date = st.date_input("تاريخ الجلسة", min_value=datetime.now().date())
                    with c2:
                        time_slots = []
                        for h in range(8, 16):
                            for m in [0, 30]:
                                if h == 15 and m == 30: continue
                                time_slots.append(f"{h:02d}:{m:02d}")
                        selected_time = st.selectbox("توقيت الجلسة", time_slots)
                    
                    submitted = st.form_submit_button("📤 نشر الجلسة وإرسال الإشعارات")
                    
                    if submitted:
                        weekday = selected_date.weekday()
                        if weekday >= 4: 
                            st.error("❌ لا يمكن جدولة جلسات في يومي الجمعة والسبت.")
                        else:
                            session_datetime_str = format_datetime_ar(selected_date, selected_time)
                            details_text = f"موعد الجلسة: {session_datetime_str}"
                            
                            target_students = get_students_of_professor(prof_name, df_memos)
                            
                            if not target_students:
                                st.warning("⚠️ لا يوجد طلاب مسجلون لديك حالياً لإرسال الإشعار.")
                            else:
                                save_success, save_msg = save_and_send_request(
                                    "جلسة إشراف", 
                                    prof_name, 
                                    "جماعي", 
                                    "جلسة إشراف", 
                                    details_text,
                                    status="منجز"
                                )
                                
                                if save_success:
                                    update_success, update_msg = update_session_date_in_sheets(prof_name, details_text)
                                    if update_success:
                                        st.success(f"✅ {save_msg}")
                                        st.info(f"تم تحديث موعد الجلسة في ملفات {len(target_students)} طالب.")
                                        
                                        email_success, email_msg = send_session_emails(target_students, details_text, prof_name)
                                        if email_success:
                                            st.success("📧 تم إرسال الإشعارات للطلبة والإدارة.")
                                        else:
                                            st.warning(f"⚠️ تم الحفظ لكن فشل الإرسال: {email_msg}")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(f"تم حفظ الطلب ولكن حدث خطأ في تحديث المذكرات: {update_msg}")
                                else:
                                    st.error(save_msg)

            with tab3:
                st.subheader("كلمات السر")
                pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
                if not pwds.empty:
                    for _, row in pwds.iterrows():
                        stat = str(row.get("تم التسجيل", "")).strip()
                        pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                        if pwd:
                            color = "#10B981" if stat == "نعم" else "#F59E0B"
                            status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                            st.markdown(f'''<div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            
            with tab4:
                if is_exhausted: st.subheader("💡 المذكرات المقترحة")
                else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
                avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                if not avail.empty:
                    for _, m in avail.iterrows():
                        st.markdown(f'''<div class="card" style="border-left: 4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
                else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# ============================================================
# فضاء الإدارة
# ===========================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_admin"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"): logout()
        st.header("📊 لوحة تحكم الإدارة")
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        memo_col = df_students["رقم المذكرة"].astype(str).str.strip()
        reg_st = (memo_col != "").sum()
        unreg_st = (memo_col == "").sum()

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{reg_st}</div><div class="kpi-label">طلاب مسجلين</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div><div class="kpi-label">طلاب غير مسجلين</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات"])
       
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل": d_memos = df_memos
            elif f_status == "مسجلة": d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else: d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            st.dataframe(d_memos, use_container_width=True, height=400)
           
        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/الاسم):")
            if q:
                name_cols = [c for c in df_students.columns if 'اسم' in c.lower() or 'لقب' in c.lower() or 'إسم' in c.lower()]
                if name_cols:
                    mask = df_students[name_cols].astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
                    f_st = df_students[mask]
                else:
                    f_st = df_students
                st.dataframe(f_st, use_container_width=True, height=400)
            else:
                st.dataframe(df_students, use_container_width=True, height=400)
               
        with tab3:
            st.subheader("توزيع الأساتذة")
            profs_list = sorted(df_memos["الأستاذ"].dropna().unique())
            sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
            if sel_p != "الكل":
                if sel_p not in df_memos["الأستاذ"].values: st.error("بيانات الأساتذة غير متاحة")
                else: st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
            else:
                if "الأستاذ" in df_memos.columns and "رقم المذكرة" in df_memos.columns and "تم التسجيل" in df_memos.columns:
                    s_df = df_memos.groupby("الأستاذ").agg(
                        إجمالي=("رقم المذكرة", "count"),
                        مسجلة=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                    ).reset_index()
                    s_df["المتاحة"] = s_df["إجمالي"] - s_df["مسجلة"]
                    s_df = s_df.rename(columns={"إجمالي": "الإجمالي", "مسجلة": "المسجلة"})
                    st.dataframe(s_df, use_container_width=True)
                else:
                    st.error("بعض الأعمدة المطلوبة مفقودة في شيت المذكرات")
                   
        with tab4:
            st.subheader("التحليل الإحصائي")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### توزيع المذكرات حسب التخصص")
                spec_dist = df_memos.groupby("التخصص").size()
                st.bar_chart(spec_dist, color="#2F6F7E")
            with col2:
                st.markdown("##### حالة التسجيل حسب التخصص")
                reg_status = df_memos.groupby("التخصص")["تم التسجيل"].apply(lambda x: (x.astype(str).str.strip() == "نعم").sum())
                st.bar_chart(reg_status, color="#FFD700")
            st.markdown("---")
            st.markdown("##### نسب التقدم العامة")
            p_df = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].copy()
            if not p_df.empty and "نسبة التقدم" in p_df.columns:
                p_df["نسبة التقدم"] = p_df["نسبة التقدم"].apply(lambda x: int(x) if str(x).isdigit() else 0)
                avg_prog = p_df["نسبة التقدم"].mean()
                st.metric("متوسط نسبة الإنجاز", f"{avg_prog:.1f}%", delta_color="normal")
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {avg_prog}%;">{avg_prog:.1f}%</div></div>', unsafe_allow_html=True)
                st.markdown("##### آخر التسجيلات")
                recent = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"].tail(5)[["رقم المذكرة", "عنوان المذكرة", "الأستاذ", "تاريخ التسجيل"]]
                st.dataframe(recent, use_container_width=True, hide_index=True)
        with tab5:
            st.subheader("تحديث البيانات والربط")
            st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل (أعمدة S و T) لأول مرة أو لإصلاح الأخطاء.")
            if st.button("🔄 بدء عملية الربط (Sync)", type="primary"):
                with st.spinner("جاري المعالجة... قد يستغرق وقتاً"):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: clear_cache_and_reload(); st.rerun()
            st.markdown("---")
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()
        with tab6:
            st.subheader("سجل الطلبات الواردة")
            st.dataframe(df_requests, use_container_width=True, height=500)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">  إشراف مسؤول الميدان الدكتور لخضر رفاف © </div>', unsafe_allow_html=True)
