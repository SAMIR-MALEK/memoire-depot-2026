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
import base64
import re
st.cache_data.clear()

# ---------------- إعداد Logging ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرات الماستر", page_icon="📘", layout="wide")

# ========================
# إعداد الموعد النهائي
# ========================
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

# ---------------- CSS ----------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
    .main { background-color: #0A1B2C; color: #ffffff; }
    .block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }

    h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #ffffff !important; }
    label, p, span { color: #ffffff !important; }
    h1 { text-align: center; }

    .stTextInput label, .stSelectbox label { color: #ffffff !important; font-weight: 600; }

    .stButton>button, button[kind="primary"], div[data-testid="stFormSubmitButton"] button {
        background-color: #2F6F7E !important; color: #ffffff !important;
        font-size: 16px; font-weight: 600; padding: 14px 32px;
        border: none !important; border-radius: 12px !important;
        cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease; width: 100%;
        text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;
    }
    .stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }

    .card {
        background: rgba(30, 41, 59, 0.95); border:1px solid rgba(255,255,255, 0.08);
        border-radius: 20px; padding: 30px; margin-bottom: 20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        border-top: 3px solid #2F6F7E; transition: transform 0.2s ease;
    }

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
    .kpi-card {
        background: linear-gradient(145deg, #1E293B, #0F172A); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 2.5rem 1rem;
        text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden;
    }
    .kpi-value { font-size: 2.5rem; font-weight: 900; color: #FFD700; margin: 15px 0; }
    .kpi-label { font-size: 1.2rem; color: #ffffff !important; font-weight: 600; margin-top: 10px; }

    .alert-card {
        background: linear-gradient(90deg, #8B4513 0%, #A0522D 100%);
        border: 1px solid #CD853F; color: white; padding: 25px; border-radius: 12px;
        box-shadow: 0 10px 20px -5px rgba(139, 69, 19, 0.4); text-align: center; font-weight: bold;
    }

    .progress-container { background-color: #0F172A; border-radius: 99px; padding: 6px; margin: 20px 0; overflow: hidden; box-shadow: inset 0 4px 6px rgba(0, 0, 0, 0.3); }
    .progress-bar {
        height: 24px; border-radius: 99px;
        background: linear-gradient(90deg, #2F6F7E 0%, #285E6B 50%, #FFD700 100%);
        box-shadow: 0 0 15px rgba(47, 111, 126, 0.5); transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255, 0.1); background: #1E293B; }
    .stDataFrame th { background-color: #0F172A; color: #FFD700; font-weight: bold; }

    .stTabs [data-baseweb="tab-list"] { gap: 2rem; padding-bottom: 15px; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; color: #94A3B8; font-weight: 600; padding: 12px 24px; border-radius: 12px; border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { background: rgba(255, 255, 255, 0.1); color: white; }
    .stTabs [aria-selected="true"] {
        background: rgba(47, 111, 126, 0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; box-shadow: 0 0 15px rgba(47, 111, 126, 0.2);
    }

    .full-view-container {
        max-width: 1000px; margin: 0 auto; padding: 40px;
        background: rgba(15,23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px; box-shadow: 0 0 40px rgba(0,0,0,0.6); overflow: hidden;
    }

    .students-grid { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 20px; margin-bottom: 30px; }

    .student-card {
        flex: 1; max-width: 450px; min-width: 300px;
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px; padding: 25px; text-align: center; transition: all 0.3s ease;
    }
    .student-card:hover { background: rgba(255, 255, 255, 0.06); border-color: #2F6F7E; }
    .memo-badge {
        display: inline-block; background: rgba(47, 111, 126, 0.2);
        color: #FFD700; padding: 6px 16px; border-radius: 20px;
        font-size: 1rem; margin-bottom: 10px; font-weight: 600;
    }
    .memo-id { font-size: 3rem; font-weight: 900; color: #2F6F7E; margin: 0; line-height: 1; }

    .diploma-status-grid { display: flex; flex-direction: column; gap: 12px !important; width: 100%; }
    .diploma-item {
        background: rgba(255,255,255,0.05); padding: 15px 20px; border-radius: 10px; margin-bottom: 0;
        display: flex; justify-content: space-between; align-items: center;
        border-right: 4px solid #2F6F7E; transition: background 0.3s;
    }
    .diploma-item:hover { background: rgba(255,255,255,0.1); }
    .status-badge {
        padding: 6px 15px; border-radius: 20px; font-size: 0.95rem; font-weight: bold;
        min-width: 100px; text-align: center;
    }
    .status-available { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-unavailable { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .status-pending { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
    
    .memo-card-title { color: #FFFFFF !important; font-size: 1.1rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets")
    st.stop()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"

STUDENTS_RANGE = "Feuille 1!A1:U1000" 
MEMOS_RANGE = "Feuille 1!A1:U1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:P1000"
REQUESTS_RANGE = "Feuille 1!A1:K1000"

ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}

EMAIL_SENDER = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD = "qptlxzunqhdcjcjt"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "domaine.dsp@univ-bba.dz"

# ---------------- دوال مساعدة ----------------
def format_arabic_date(date_input):
    try:
        if isinstance(date_input, str):
            date_obj = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
        elif isinstance(date_input, datetime):
            date_obj = date_input
        else:
            return str(date_input)
        day = date_obj.day
        year = date_obj.year
        months_map = {1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل", 5: "ماي", 6: "جوان", 7: "جويلية", 8: "أوت", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"}
        month_name = months_map.get(date_obj.month, date_obj.strftime('%B'))
        return f"{day:02d} {month_name} {year}"
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return str(date_input)

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

# دالة جديدة لتوحيد النصوص (إزالة .0 والمسافات)
def normalize_text(val):
    v = str(val).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def validate_username(username):
    username = sanitize_input(username)
    if not username: return False, "⚠️ اسم المستخدم فارغ"
    return True, username

def validate_note_number(note_number):
    note_number = sanitize_input(note_number)
    if not note_number: return False, "⚠️ رقم المذكرة فارغ"
    if len(note_number) > 20: return False, "⚠️ رقم المذكرة غير صالح"
    return True, note_number

def is_phone_valid(phone_val):
    val = str(phone_val).strip()
    invalid_values = ['', '0', '-', 'nan', 'None', 'NaN', '.0', '0.0']
    if val in invalid_values: return False, "قيمة فارغة أو غير صالحة (0/-)"
    cleaned = val.replace(' ', '').replace('-', '')
    if not cleaned.isdigit(): return False, "لا يحتوي على أرقام فقط"
    if len(cleaned) < 9: return False, "رقم قصير جداً"
    return True, "صالح"

def is_nin_valid(nin_val):
    val = str(nin_val).strip().replace('.0', '')
    invalid_values = ['', '0', '-', 'nan', 'None', 'NaN']
    if val in invalid_values: return False, "قيمة فارغة أو غير صالحة (0/-)"
    if not val.isdigit(): return False, "يجب أن يحتوي على أرقام فقط"
    return True, "صالح"

def get_student_name_display(student_dict):
    keys_lname = ["لقب", "اللقب", ""]
    lname = ""
    for k in keys_lname:
        if k in student_dict and str(student_dict[k]).strip() not in ['nan', '']:
            lname = student_dict[k]
            break
    
    keys_fname = ["إسم", "اسم", "الإسم", ""]
    fname = ""
    for k in keys_fname:
        if k in student_dict and str(student_dict[k]).strip() not in ['nan', '']:
            fname = student_dict[k]
            break
            
    return lname, fname

def get_email_smart(row):
    if isinstance(row, dict):
        priority_keys = ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]
        for key in priority_keys:
            val = str(row.get(key, "")).strip()
            if "@" in val and val != "nan": return val
        for val in row.values():
            v = str(val).strip()
            if "@" in v and v != "nan": return v
        return ""
    try:
        values_list = row.tolist()
        for i in range(9, 13):
            if i < len(values_list):
                val = str(values_list[i]).strip()
                if "@" in val and val != "nan": return val
        for col in row.index:
            clean_col_name = str(col).strip()
            if clean_col_name in ["البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]:
                val = str(row[col]).strip()
                if "@" in val and val != "nan": return val
        return ""
    except:
        return ""

def get_student_info_from_memo(memo_row, df_students):
    student1_name = str(memo_row.get("الطالب الأول", "")).strip()
    student2_name = str(memo_row.get("الطالب الثاني", "")).strip()
    s1_email = s2_email = s1_reg_display = s2_reg_display = ""
    email_fetcher = get_email_smart
    try:
        memo_list = memo_row.tolist()
        raw_reg1 = str(memo_list[18]).strip() if len(memo_list) > 18 else ""
        raw_reg2 = str(memo_list[19]).strip() if len(memo_list) > 19 else ""
        reg1 = normalize_text(raw_reg1) # استخدام normalize_text
        reg2 = normalize_text(raw_reg2) # استخدام normalize_text
    except:
        reg1 = normalize_text(memo_row.get("رقم تسجيل الطالب 1", ""))
        reg2 = normalize_text(memo_row.get("رقم تسجيل الطالب 2", ""))
        
    # Normalize registration numbers in the dataframe for matching
    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)

    if reg1:
        s_data = df_students[df_students["رقم التسجيل_norm"] == reg1]
        if not s_data.empty:
            s1_email = email_fetcher(s_data.iloc[0])
            s1_reg_display = reg1
    if student2_name and reg2:
        s_data = df_students[df_students["رقم التسجيل_norm"] == reg2]
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

def update_student_profile(username, phone, nin):
    try:
        df_students = load_students()
        # Use normalized matching for username lookup as well
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        username_norm = normalize_text(username)
        
        student_row = df_students[df_students["username_norm"] == username_norm]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        
        # Original index for sheet update
        row_idx = student_row.index[0] + 2
        updates = [
            {"range": f"Feuille 1!M{row_idx}", "values": [[phone]]},
            {"range": f"Feuille 1!U{row_idx}", "values": [[nin]]}
        ]
        
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=STUDENTS_SHEET_ID, 
            body=body
        ).execute()
        
        clear_cache_and_reload()
        return True, "✅ تم تحديث البيانات بنجاح"
    except Exception as e:
        logger.error(f"خطأ في تحديث الملف: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التحديث: {str(e)}"

def sync_student_registration_numbers():
    try:
        st.info("⏳ جاري بدء عملية الربط...")
        df_s = load_students()
        df_m = load_memos()
        updates = []
        
        # Normalize for matching
        df_s['رقم المذكرة_norm'] = df_s['رقم المذكرة'].astype(str).apply(normalize_text)
        
        students_with_memo = df_s[df_s['رقم المذكرة_norm'].notna() & (df_s['رقم المذكرة_norm'] != "")]
        
        for index, row in df_m.iterrows():
            memo_num = normalize_text(row.get("رقم المذكرة", ""))
            if not memo_num: continue
            
            matched_students = students_with_memo[students_with_memo["رقم المذكرة_norm"] == memo_num]
            if matched_students.empty: continue
            
            s1_name = str(row.get("الطالب الأول", "")).strip()
            s2_name = str(row.get("الطالب الثاني", "")).strip()
            reg_s1 = ""; reg_s2 = ""
            
            for _, s_row in matched_students.iterrows():
                lname = s_row.get('لقب', s_row.get('اللقب', ''))
                fname = s_row.get('إسم', s_row.get('الإسم', ''))
                full_name = f"{lname} {fname}".strip()
                if full_name == s1_name: reg_s1 = normalize_text(s_row.get("رقم التسجيل", ""))
                elif s2_name and full_name == s2_name: reg_s2 = normalize_text(s_row.get("رقم التسجيل", ""))
            
            if not reg_s1 and len(matched_students) > 0: reg_s1 = normalize_text(matched_students.iloc[0].get("رقم التسجيل", ""))
            
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
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = ["", timestamp, req_type, status, prof_name, memo_id, "", "", details_text, "", ""]
        body_append = {"values": [new_row]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2",
            valueInputOption="USER_ENTERED", body=body_append, insertDataOption="INSERT_ROWS"
        ).execute()
        
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
        # Normalize for matching
        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == normalize_text(memo_number)]
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

# -------------------------------------------------------------
# دوال الإيميل
# -------------------------------------------------------------
def _send_email_to_professor_row(row):
    possible_username_keys = ["إسم المستخدم", "اسم المستخدم", "Identifiant", "Username", "user"]
    possible_password_keys = ["كلمة المرور", "كلمة السر", "Password", "pass"]
    possible_email_keys = ["البريد الإلكتروني", "الإيميل", "email", "Email", "E-mail"]
    
    prof_name = row.get("الأستاذ", "غير محدد")
    email = ""; username = ""; password = ""
    
    for col in possible_email_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if "@" in val and val != "nan": email = val; break
            
    for col in possible_username_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val != "": username = val; break
            
    for col in possible_password_keys:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val != "": password = val; break
            
    if not email or not username or not password: return False, "⚠️ بيانات ناقصة"
    
    email_body = f"""
    <html dir="rtl"><head><meta charset="UTF-8"><style>body {{ font-family: 'Cairo', Arial, sans-serif; direction: rtl; text-align: right; line-height: 1.6; background-color: #f4f4f4; margin: 0; padding: 0; }} .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 30px; border: 1px solid #dddddd; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }} .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #0056b3; padding-bottom: 20px; }} .header h2 {{ color: #003366; margin: 0; font-size: 24px; }} .header h3 {{ color: #005580; margin: 5px 0 0 0; font-size: 20px; }} .content {{ margin-bottom: 30px; color: #333; }} .content ul {{ padding-right: 20px; }} .info-box {{ background-color: #eef7fb; border-right: 5px solid #005580; padding: 20px; margin: 20px 0; border-radius: 4px; }} .info-box p {{ margin: 10px 0; font-weight: bold; font-size: 1.1em; }} .footer {{ text-align: center; margin-top: 40px; font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px; }} .link {{ color: #005580; text-decoration: none; font-weight: bold; }} .link:hover {{ text-decoration: underline; }}</style></head><body><div class="container"><div class="header"><h2>جامعة محمد البشير الإبراهيمي – برج بوعريريج</h2><h3>كلية الحقوق والعلوم السياسية</h3><h4 style="color:#666; margin-top:5px;">فضاء الأساتذة</h4></div><div class="content"><p>تحية طيبة وبعد،</p><p>الأستاذ (ة) الفاضل (ة) : <strong>{prof_name}</strong></p><br><p>في إطار رقمنة متابعة مذكّرات الماستر، يشرفنا إعلامكم بأنه تم تفعيل فضاء الأساتذة على منصة متابعة مذكرات الماستر الخاصة بكلية الحقوق والعلوم السياسية، وذلك قصد تسهيل عملية المتابعة البيداغوجية وتنظيم الإشراف.</p><p>يُمكِّنكم فضاء الأستاذ من القيام بالمهام التالية:</p><ul><li>متابعة حالة تسجيل كل مذكرة (مسجلة / غير مسجلة).</li><li>الاطلاع على أسماء الطلبة المسجلين وأرقام هواتفهم وبريدهم المهني.</li><li>تحديث نسبة التقدم في إنجاز المذكرات.</li><li>تحديد موعد جلسة إشراف واحدة يتم تعميمها آليًا على جميع الطلبة المعنيين.</li><li>إرسال طلبات إدارية رقمية للإدارة.</li></ul><div class="info-box"><p>الدخول إلى حسابكم يكون عبر الرابط:</p><a href="https://memoires2026.streamlit.app" class="link">https://memoires2026.streamlit.app</a><p style="margin-top: 15px;">إسم المستخدم: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{username}</span></p><p>كلمة المرور: <span style="background:#fff; padding:2px 8px; border:1px solid #ccc; border-radius:4px;">{password}</span></p></div></div><div class="footer"><p>تقبلوا تحياتنا الطيبة.</p><p>مسؤول الميدان: البروفيسور لخضر رفاف</p></div></div></body></html>
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = email; msg['Subject'] = "تفعيل حساب فضاء الأساتذة - منصة المذكرات"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, f"✅ تم الإرسال إلى {email}"
    except Exception as e:
        logger.error(f"Error sending email to {prof_name}: {e}")
        return False, f"❌ فشل الإرسال: {str(e)}"

def send_welcome_emails_to_all_profs():
    try:
        df_profs = load_prof_memos()
        sent_count = 0; failed_count = 0; results_log = []
        progress_bar = st.progress(0); total_profs = len(df_profs)
        with st.spinner("⏳ جاري الإرسال لجميع الأساتذة... يرجى الانتظار"):
            for index, row in df_profs.iterrows():
                success, msg = _send_email_to_professor_row(row)
                if success: sent_count += 1
                else: failed_count += 1
                results_log.append(msg)
                progress_bar.progress((index + 1) / total_profs)
                time.sleep(0.5)
        return sent_count, failed_count, results_log
    except Exception as e:
        return 0, 0, [f"خطأ عام: {str(e)}"]

def send_welcome_email_to_one(prof_name):
    try:
        df_profs = load_prof_memos()
        prof_rows = df_profs[df_profs["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_rows.empty: return False, f"❌ لم يتم العثور على الأستاذ: {prof_name}"
        row = prof_rows.iloc[0]
        with st.spinner(f"⏳ جاري الإرسال للأستاذ: {prof_name}..."):
            success, msg = _send_email_to_professor_row(row)
        if success: return True, msg
        else: return False, msg
    except Exception as e:
        logger.error(f"Error sending single email: {e}")
        return False, f"حدث خطأ: {str(e)}"

def format_datetime_ar(date_obj, time_str):
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    day_name = days_ar[date_obj.weekday()]
    date_str = date_obj.strftime('%Y-%m-%d')
    return f"{day_name} {date_str} الساعة {time_str}"

def get_students_of_professor(prof_name, df_memos):
    prof_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")]
    students_data = []
    for _, memo in prof_memos.iterrows():
        s1_name = str(memo.get("الطالب الأول", "")).strip()
        s1_reg = normalize_text(memo.get("رقم تسجيل الطالب 1", memo.get("رقم التسجيل 1", "")))
        if s1_name and s1_name != "--" and s1_reg: students_data.append({"name": s1_name, "reg": s1_reg, "memo": memo.get("رقم المذكرة")})
        
        s2_name = str(memo.get("الطالب الثاني", "")).strip()
        s2_reg = normalize_text(memo.get("رقم تسجيل الطالب 2", memo.get("رقم التسجيل 2", "")))
        if s2_name and s2_name != "--" and s2_reg: students_data.append({"name": s2_name, "reg": s2_reg, "memo": memo.get("رقم المذكرة")})
    return students_data

def update_session_date_in_sheets(prof_name, date_str):
    try:
        df_memos = load_memos()
        masks = (df_memos["الأستاذ"].astype(str).str.strip() == prof_name) & (df_memos["تم التسجيل"].astype(str).str.strip() == "نعم")
        target_indices = df_memos[masks].index
        if target_indices.empty: return True, "لا توجد مذكرات لتحديثها"
        
        updates = []; col_names = df_memos.columns.tolist(); target_col_name = "موعد الجلسة القادمة"
        if target_col_name in col_names: col_idx = col_names.index(target_col_name) + 1
        else: col_idx = len(col_names)
        col_letter_str = col_letter(col_idx)
        
        for idx in target_indices:
            row_num = idx + 2
            updates.append({"range": f"Feuille 1!{col_letter_str}{row_num}", "values": [[date_str]]})
        
        body = {"valueInputOption": "USER_ENTERED", "data": updates}
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body=body).execute()
        return True, "تم تحديث التواريخ بنجاح"
    except Exception as e:
        logger.error(f"Update Session Error: {e}")
        return False, str(e)

def send_session_emails(students_data, session_info, prof_name):
    try:
        df_students = load_students(); student_emails = []
        
        # Create normalized column for matching
        df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
        
        for s in students_data:
            s_row = df_students[df_students["رقم التسجيل_norm"] == s['reg']]
            if not s_row.empty:
                email = ""
                possible_cols = ["البريد المهني", "البريد الإلكتروني", "email", "Email"]
                for col in possible_cols:
                    if col in s_row.columns:
                        val = str(s_row.iloc[0][col]).strip()
                        if val and val != "nan" and "@" in val: email = val; break
                if email: student_emails.append(email)
        
        subject = f"🔔 تنبيه هام: جلسة إشراف - {prof_name}"
        students_list_html = "<ul>"
        for i, s in enumerate(students_data):
            if i < 10: students_list_html += f"<li>{s['name']}</li>"
            else: students_list_html += f"<li>... و {len(students_data) - 10} طالب آخر</li>"; break
        students_list_html += "</ul>"
        
        email_body = f"""
        <html dir="rtl"><head><style>body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }} .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; border-top: 5px solid #256D85; }} .header {{ text-align: center; margin-bottom: 20px; }} .highlight {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; font-size: 1.1em; }} .footer {{ text-align: center; color: #777; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}</style></head><body><div class="container"><div class="header"><h2 style="color: #256D85; margin: 0;">📅 جدولة جلسة إشراف</h2></div><p>السلام عليكم ورحمة الله،</p><p>يُعلن الأستاذ(ة) <b>{prof_name}</b> عن تنظيم جلسة إشراف للمذكرات.</p><div class="highlight"><strong>📆 الموعد:</strong> {session_info}</div><p>تم توجيه هذا الإشعار إلى الطلبة المسجلين تحت إشراف الأستاذ:</p>{students_list_html}<hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"><p style="font-size: 0.9em; color: #555;"><strong>للإدارة:</strong> يرجى نشر هذا الموعد في الفيسبوك وإعلام الطلبة غير الحاصلين على بريد إلكتروني.</p></div><div class="footer">جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية</div></body></html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = ADMIN_EMAIL; msg['Subject'] = subject
        if student_emails: msg['Bcc'] = ", ".join(student_emails)
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        logger.info(f"✅ Session email sent to Admin and {len(student_emails)} students.")
        return True, "تم الإرسال"
    except Exception as e:
        logger.error(f"Error sending session emails: {e}")
        return False, str(e)

def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    try:
        df_prof_memos = load_prof_memos()
        prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        if prof_row.empty:
            clean_name = prof_name.strip().replace("الأستاذ", "").replace("د.", "").replace("أ.د", "").strip()
            if clean_name: prof_row = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.contains(clean_name, case=False, na=False)]
        
        if prof_row.empty:
            error_msg = f"فشل الإرسال: لم يتم العثور على البريد للأستاذ <b>{prof_name}</b>."
            logger.error(f"Email Error: Professor {prof_name} not found.")
            return False, error_msg
            
        prof_data = prof_row.iloc[0]; prof_email = ""
        possible_email_cols = ["البريد الإلكتروني", "الإيميل", "email", "Email"]
        for col in possible_email_cols:
            if col in prof_data.index:
                val = str(prof_data[col]).strip()
                if val and val != "nan": prof_email = val; break
        
        if "@" not in prof_email:
            error_msg = f"فشل الإرسال: الأستاذ <b>{prof_name}</b> موجود، ولكن البريد الإلكتروني فارغ."
            logger.error(f"Email Error: Invalid email for Prof {prof_name}: {prof_email}")
            return False, error_msg
            
        total_memos = len(prof_row)
        registered_memos = len(prof_row[prof_row["تم التسجيل"].astype(str).str.strip() == "نعم"])
        
        s1_lname, s1_fname = get_student_name_display(student1)
        student2_info = ""
        if student2 is not None:
            s2_lname, s2_fname = get_student_name_display(student2)
            student2_info = f"\n👤 **الطالب الثاني:** {s2_lname} {s2_fname}"
            
        email_body = f"""
<html dir="rtl"><head><style>body {{ font-family: 'Arial', sans-serif; background-color: #f4f4f4; padding: 20px; }} .container {{ background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }} .header {{ background-color: #256D85; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }} .header h2 {{ margin: 0; }} .content {{ line-height:1.8; color: #333; }} .info-box {{ background-color: #f8f9fa; padding: 15px; border-right: 4px solid #256D85; margin: 15px 0; }} .stats-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0; }} .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }} .highlight {{ color: #256D85; font-weight: bold; }} ul {{ list-style: none; padding: 0; }} li {{ padding: 5px 0; }}</style></head>
<body><div class="container"><div class="header"><h2>✅ تسجيل مذكرة جديدة</h2></div><div class="content"><p>تحية طيبة، الأستاذ(ة) <span class="highlight">{prof_name}</span>،</p><p>نحيطكم علماً بأنه تم تسجيل مذكرة جديدة تحت إشرافكم:</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p><p>📑 <strong>عنوان المذكرة:</strong> {memo_info['عنوان المذكرة']}</p><p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p><p>👤 <strong>الطالب الأول:</strong> {s1_lname} {s1_fname}{student2_info}</p><p>🕒 <strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div><div class="stats-box"><h3 style="color: #256D85; margin-top: 0;">📊 إحصائيات مذكراتك:</h3><ul><li>📝 <strong>إجمالي المذكرات:</strong> {total_memos}</li><li>✅ <strong>المذكرات المسجلة:</strong> {registered_memos}</li><li>⏳ <strong>المذكرات المتبقية:</strong> {total_memos - registered_memos}</li></ul></div><p style="margin-top: 20px; color: #666;">للاستفسار والدعم، يرجى التواصل مع مسؤول الميدان البروفيسور رفاف لخضر.</p></div><div class="footer"><p>© 2026 جامعة محمد البشير الإبراهيمي</p></div></div></body></html>
"""
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER; msg['To'] = prof_email
        msg['Subject'] = f"✅ تسجيل مذكرة جديدة - رقم {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(email_body, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        logger.info(f"✅ Email sent to professor {prof_name}")
        return True, "تم إرسال البريد الإلكتروني بنجاح"
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}")
        return False, f"خطأ تقني أثناء الإرسال: {str(e)}"

# ---------------- دوال التحقق (محدثة) ----------------
def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result
    password = sanitize_input(password)
    if df_students.empty: return False, "❌ خطأ في تحميل بيانات الطلاب"
    
    # التحقق من وجود العمود أولاً
    if "اسم المستخدم" not in df_students.columns:
        return False, "❌ خطأ في بنية البيانات: عمود اسم المستخدم غير موجود"

    # التصحيح: تطبيق normalize_text على العمود بأكمله قبل المقارنة
    # هذا يضمن إزالة .0 والمسافات الزائدة من القيم الرقمية
    db_usernames = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
    
    # إنشاء قناع (mask) للمطابقة
    student_mask = db_usernames == username
    
    student = df_students[student_mask]
    
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    
    # التحقق من كلمة السر
    db_password = str(student.iloc[0]["كلمة السر"]).strip()
    if db_password != password: return False, "❌ كلمة السر غير صحيحة"
    
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
    if any(col not in df_prof_memos.columns for col in required_cols): 
        return False, f"❌ الأعمدة التالية غير موجودة: {', '.join([col for col in required_cols if col not in df_prof_memos.columns])}"
    
    # التصحيح: تطبيق normalize_text هنا أيضاً
    db_prof_usernames = df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text)
    
    prof_mask = (db_prof_usernames == username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip() == password)
    prof = df_prof_memos[prof_mask]
    
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
    
    # التصحيح: normalize memo number
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_number]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    
    memo_row = memo_row.iloc[0]
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0].to_dict(), None

# ============================================================
# الدالة: تحديث التسجيل
# ============================================================
def update_registration(note_number, student1, student2=None, s2_new_phone=None, s2_new_nin=None):
    try:
        df_memos = load_memos()
        df_prof_memos = load_prof_memos()
        df_students = load_students()

        memo_data_main = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()]
        if memo_data_main.empty:
            return False, "❌ رقم المذكرة غير موجود في القائمة الرئيسية"
        
        prof_name = memo_data_main["الأستاذ"].iloc[0].strip()
        used_prof_password = st.session_state.prof_password.strip()
        
        potential_rows = df_prof_memos[
            (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) & 
            (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == used_prof_password)
        ]
        if potential_rows.empty: return False, "❌ بيانات الأستاذ أو كلمة السر غير متطابقة في شيت المتابعة"
        
        # Check if memo already registered in prof sheet to avoid duplicates
        target_row = potential_rows[potential_rows["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()]
        if target_row.empty:
            # If memo number not in prof sheet yet, find an empty slot (unregistered row)
            target_row = potential_rows[potential_rows["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if target_row.empty: return False, "❌ خطأ: جميع المذكرات المخصصة لهذا الأستاذ مسجلة بالفعل."
            
        prof_row_idx = target_row.index[0] + 2 
        col_names = df_prof_memos.columns.tolist()
        
        s1_lname, s1_fname = get_student_name_display(student1)
        
        updates = [
            {"range": f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
        ]
        
        if student2 is not None:
            s2_lname, s2_fname = get_student_name_display(student2)
            updates.append({"range": f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates}).execute()
        
        # Update Main Memos Sheet
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()].index[0] + 2
        memo_cols = df_memos.columns.tolist()
        
        reg1 = normalize_text(student1.get('رقم التسجيل', ''))
        reg2 = normalize_text(student2.get('رقم التسجيل', '')) if student2 else ""
        
        updates2 = [
            {"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[s1_lname + ' ' + s1_fname]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
            {"range": f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range": f"Feuille 1!S{memo_row_idx}", "values": [[reg1]]}
        ]
        if 'كلمة سر التسجيل' in memo_cols: 
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}", "values": [[used_prof_password]]})
        if student2 is not None:
            updates2.append({"range": f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[s2_lname + ' ' + s2_fname]]})
            updates2.append({"range": f"Feuille 1!T{memo_row_idx}", "values": [[reg2]]})
            
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": updates2}).execute()
        
        # Update Students Sheet
        students_cols = df_students.columns.tolist()
        
        # Find student row using normalized username
        s1_user = normalize_text(student1.get('اسم المستخدم', ''))
        student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == s1_user].index[0] + 2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student1_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
        
        if student2 is not None:
            s2_user = normalize_text(student2.get('اسم المستخدم', ''))
            student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == s2_user].index[0] + 2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{student2_row_idx}", valueInputOption="USER_ENTERED", body={"values": [[note_number]]}).execute()
            
            s2_updates = []
            if s2_new_phone:
                 s2_updates.append({"range": f"Feuille 1!M{student2_row_idx}", "values": [[s2_new_phone]]})
            if s2_new_nin:
                 s2_updates.append({"range": f"Feuille 1!U{student2_row_idx}", "values": [[s2_new_nin]]})
            
            if s2_updates:
                sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=STUDENTS_SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": s2_updates}).execute()

        time.sleep(2)
        clear_cache_and_reload()
        time.sleep(1)
        
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text) == s1_user].iloc[0].to_dict()
        if student2 is not None: 
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text) == s2_user].iloc[0].to_dict()
            
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == str(note_number).strip()].iloc[0]
        email_sent, email_msg = send_email_to_professor(prof_name, memo_data, st.session_state.student1, st.session_state.student2 if student2 else None)
        if not email_sent: st.error(f"⚠️ {email_msg}"); st.warning("تم تسجيل المذكرة في النظام، لكن لم يتم إرسال الإيميل للأستاذ.")
        else: st.success("📧 تم إرسال إشعار بالبريد الإلكتروني للأستاذ.")
        
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"خطأ في تحديث التسجيل: {str(e)}")
        return False, f"❌ حدث خطأ أثناء التسجيل: {str(e)}"

# ============================================================
# دالة تحديث ملف التخرج (للإدارة)
# ============================================================
def update_diploma_status(username, status_dict):
    try:
        df_students = load_students()
        username_norm = normalize_text(username)
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        
        student_row = df_students[df_students["username_norm"] == username_norm]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        
        row_idx = student_row.index[0] + 2
        updates = []
        cols_map = {'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20}
        
        for col_letter_name, val in status_dict.items():
            if col_letter_name in cols_map:
                updates.append({"range": f"Feuille 1!{col_letter_name}{row_idx}", "values": [[val]]})
        
        if updates:
            body = {"valueInputOption": "USER_ENTERED", "data": updates}
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=STUDENTS_SHEET_ID, 
                body=body
            ).execute()
            clear_cache_and_reload()
            return True, "✅ تم تحديث ملف التخرج بنجاح"
        return False, "لم يتم تحديث أي بيانات"
    except Exception as e:
        logger.error(f"خطأ في تحديث ملف التخرج: {str(e)}")
        return False, f"❌ حدث خطأ: {str(e)}"

# ============================================================
# جلب البيانات
# ============================================================
df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty: st.error("❌ خطأ في تحميل البيانات. يرجى المحاولة لاحقاً."); st.stop()

# ============================================================
# دوال استعادة الجلسة
# ============================================================
def encode_str(s): return base64.urlsafe_b64encode(s.encode()).decode()
def decode_str(s): 
    try: return base64.urlsafe_b64decode(s.encode()).decode()
    except: return ""

def lookup_student(username):
    if df_students.empty: return None
    # Use normalized matching
    s = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text) == normalize_text(username)]
    if not s.empty: return s.iloc[0].to_dict()
    return None

def restore_session_from_url():
    if st.session_state.get('logged_in', False): return
    qp = st.query_params
    if 'ut' in qp and 'un' in qp:
        user_type_raw = qp['ut']; username_raw = qp['un']
        user_type = user_type_raw if isinstance(user_type_raw, str) else (user_type_raw[0] if isinstance(user_type_raw, list) and user_type_raw else "")
        username_enc = username_raw if isinstance(username_raw, str) else (username_raw[0] if isinstance(username_raw, list) and username_raw else "")
        username = decode_str(username_enc)
        if not username: return
        
        if user_type == 'student':
            s_data = lookup_student(username)
            if s_data:
                s_nin = normalize_text(s_data.get('NIN', ''))
                s_phone = str(s_data.get('الهاتف', '')).strip()
                
                nin_valid, _ = is_nin_valid(s_nin)
                phone_valid, _ = is_phone_valid(s_phone)
                
                if nin_valid and phone_valid:
                    st.session_state.user_type = 'student'
                    st.session_state.student1 = s_data
                    note_num = normalize_text(s_data.get('رقم المذكرة', ''))
                    st.session_state.mode = "view" if note_num else "register"
                    st.session_state.logged_in = True
                    if note_num:
                        memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_num]
                        if not memo_row.empty:
                            memo_row = memo_row.iloc[0]
                            s2_name = str(memo_row.get("الطالب الثاني", "")).strip()
                            if s2_name and s2_name != "--":
                                s2_reg = normalize_text(memo_row.get("رقم تسجيل الطالب 2", ""))
                                if s2_reg:
                                    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
                                    s2_data = df_students[df_students["رقم التسجيل_norm"] == s2_reg]
                                    if not s2_data.empty: st.session_state.student2 = s2_data.iloc[0].to_dict()
                else:
                     st.session_state.user_type = 'student'
                     st.session_state.profile_incomplete = True
                     st.session_state.profile_user_temp = s_data
                     
        elif user_type == 'professor':
            # Normalize prof username check
            p_data = df_prof_memos[df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text) == normalize_text(username)]
            if not p_data.empty: st.session_state.professor = p_data.iloc[0].to_dict(); st.session_state.logged_in = True
        elif user_type == 'admin':
            if username in ADMIN_CREDENTIALS: st.session_state.admin_user = username; st.session_state.logged_in = True
        if user_type: st.session_state.user_type = user_type

restore_session_from_url()

required_state = {
    'user_type': None, 'logged_in': False, 'student1': None, 'student2': None,
    'professor': None, 'admin_user': None, 'memo_type': "فردية",
    'mode': "register", 'note_number': "", 'prof_password': "",
    'show_confirmation': False, 'selected_memo_id': None,
    'admin_edit_student_user': None, 's2_phone_input': "", 's2_nin_input': "",
    'profile_incomplete': False, 'profile_user_temp': None, 'profile_error_msg': None
}
for key, value in required_state.items():
    if key not in st.session_state: st.session_state[key] = value

def logout():
    st.query_params.clear()
    keys_to_del = list(st.session_state.keys())
    for key in keys_to_del:
         del st.session_state[key]
    for key, value in required_state.items():
        st.session_state[key] = value
    st.rerun()

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
    if st.session_state.get('profile_incomplete', False):
        st.markdown("<h2>⚠️ استكمال الملف الشخصي</h2>", unsafe_allow_html=True)
        error_msg = st.session_state.get('profile_error_msg', "بيانات ناقصة")
        st.error(f"يجب إدخال المعلومات الناقصة:")
        st.markdown(f"<div style='background:rgba(255,0,0,0.1); padding:10px; border-radius:5px; color:#FF6B6B; margin-bottom:20px;'>{error_msg}</div>", unsafe_allow_html=True)
        temp_data = st.session_state.profile_user_temp
        
        with st.form("complete_profile_form"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            default_phone = str(temp_data.get('الهاتف', '')).strip()
            if default_phone in ['0', '0.0', 'nan', '-']: default_phone = ""
            default_nin = normalize_text(temp_data.get('NIN', ''))
            if default_nin in ['0', 'nan', '-']: default_nin = ""

            new_phone = st.text_input("📞 أدخل رقم هاتف صحيح (10 أرقام)", value=default_phone)
            new_nin = st.text_input("🆔 أدخل رقم التعريف الوطني (18 رقم)", value=default_nin)
            submitted = st.form_submit_button("💾 حفظ البيانات والمتابعة", type="primary", use_container_width=True)
            
            if submitted:
                phone_ok, _ = is_phone_valid(new_phone)
                nin_ok, _ = is_nin_valid(new_nin)
                if not phone_ok: st.error("❌ رقم الهاتف غير صالح.")
                elif not nin_ok: st.error("❌ الرقم الوطني غير صحيح.")
                else:
                    username = normalize_text(temp_data.get('اسم المستخدم', ''))
                    success, msg = update_student_profile(username, new_phone, new_nin)
                    if success:
                        st.success(msg)
                        st.session_state.profile_error_msg = None
                        st.session_state.profile_incomplete = False
                        st.session_state.logged_in = True
                        df_updated = load_students()
                        st.session_state.student1 = df_updated[df_updated["اسم المستخدم"].astype(str).apply(normalize_text) == username].iloc[0].to_dict()
                        note_num = normalize_text(st.session_state.student1.get('رقم المذكرة', ''))
                        if note_num: st.session_state.mode = "view"
                        else: st.session_state.mode = "register"
                        st.rerun()
                    else: st.error(msg)
            st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_student"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>فضاء الطلبة</h2>", unsafe_allow_html=True)
        
        with st.form("student_login_form"):
            st.write("### 🔐 تسجيل الدخول")
            username1 = st.text_input("اسم المستخدم")
            password1 = st.text_input("كلمة السر", type="password")
            submitted = st.form_submit_button("دخول")
            if submitted:
                valid, result = verify_student(username1, password1, df_students)
                if not valid:
                    st.error(result)
                else:
                    s_phone = str(result.get('الهاتف', '')).strip()
                    s_nin = normalize_text(result.get('NIN', ''))
                    phone_ok, phone_msg = is_phone_valid(s_phone)
                    nin_ok, nin_msg = is_nin_valid(s_nin)
                    
                    if phone_ok and nin_ok:
                        st.session_state.student1 = result
                        note_num = normalize_text(st.session_state.student1.get('رقم المذكرة', ''))
                        if note_num:
                            st.session_state.mode = "view"
                            memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == note_num]
                            if not memo_row.empty:
                                memo_row = memo_row.iloc[0]
                                s2_name = str(memo_row.get("الطالب الثاني", "")).strip()
                                if s2_name and s2_name != "--":
                                    s2_reg = normalize_text(memo_row.get("رقم تسجيل الطالب 2", ""))
                                    if s2_reg:
                                        df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
                                        s2_data = df_students[df_students["رقم التسجيل_norm"] == s2_reg]
                                        if not s2_data.empty: st.session_state.student2 = s2_data.iloc[0].to_dict()
                        else:
                            st.session_state.mode = "register"
                        st.session_state.logged_in = True
                        st.query_params['ut'] = 'student'
                        st.query_params['un'] = encode_str(normalize_text(result.get('اسم المستخدم', '')))
                        st.rerun()
                    else:
                        error_details = []
                        if not phone_ok: error_details.append(f"الهاتف الحالي ('{s_phone}') غير صالح: {phone_msg}")
                        if not nin_ok: error_details.append(f"أدخل رقم التعريف الوطني (18 رقما)")
                        st.session_state.student1 = result
                        st.session_state.profile_user_temp = result
                        st.session_state.profile_incomplete = True
                        st.session_state.profile_error_msg = "<br>".join(error_details)
                        st.rerun()
    
    else:
        s1 = st.session_state.student1; s2 = st.session_state.student2
        if st.session_state.mode == "register":
            st.markdown("<div class='alert-card'>📝 مرحباً بك، أنت غير مسجل في مذكرة بعد.</div>", unsafe_allow_html=True)
            st.markdown("---")
            registration_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"], horizontal=True)
            
            username2 = password2 = None
            student2_obj = None
            s2_missing_info = False
            s2_new_phone_val = ""
            s2_new_nin_val = ""

            if registration_type == "ثنائية":
                st.markdown("### 👥 بيانات الطالب الثاني")
                username2 = st.text_input("اسم المستخدم الطالب الثاني")
                password2 = st.text_input("كلمة السر الطالب الثاني", type="password")
                
                if username2 and password2:
                    v2, r2 = verify_student(username2, password2, df_students)
                    if v2:
                        student2_obj = r2
                        s2_phone = str(r2.get('الهاتف', '')).strip()
                        s2_nin = normalize_text(r2.get('NIN', ''))
                        s2_phone_ok, s2_phone_msg = is_phone_valid(s2_phone)
                        s2_nin_ok, s2_nin_msg = is_nin_valid(s2_nin)
                        if not s2_phone_ok or not s2_nin_ok:
                            s2_missing_info = True
                            st.warning(f"⚠️ الطالب الثاني ({r2.get('لقب')} {r2.get('إسم')}) لم يستكمل ملفه الشخصي. يرجى إدخال بياناته أدناه للمتابعة.")
                            s2_new_phone_val = st.text_input("📞 هاتف الطالب الثاني", value=s2_phone, key="s2_phone_input_new")
                            s2_new_nin_val = st.text_input("🆔 NIN الطالب الثاني", value=s2_nin, key="s2_nin_input_new")
                            if s2_new_phone_val and s2_new_nin_val:
                                tmp_ph_ok, _ = is_phone_valid(s2_new_phone_val)
                                tmp_nin_ok, _ = is_nin_valid(s2_new_nin_val)
                                if tmp_ph_ok and tmp_nin_ok: st.info("✅ بيانات الطالب الثاني جاهزة للحفظ عند التسجيل.")
                                else:
                                    st.error("❌ صيغة الهاتف أو NIN غير صحيحة للطالب الثاني.")
                                    student2_obj = None
                        else: st.success("✅ بيانات الطالب الثاني كاملة.")
                    else: st.error(r2)
            
            st.markdown("### 🔍 البحث عن مذكرة متاحة")
            student_specialty = str(s1.get("التخصص", "")).strip()
            
            def clean_text(val):
                v = str(val).strip()
                if v in ['', 'nan', 'None', 'NaN', '-', '0', '0.0']: return ''
                return v

            prof_counts = df_prof_memos.groupby("الأستاذ")["رقم المذكرة"].apply(
                lambda x: sum([1 for val in x if clean_text(val) != ''])
            ).to_dict()
            
            available_memos_df = df_memos[
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم") & 
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty)
            ]
            
            available_profs = []
            if not available_memos_df.empty:
                profs_in_list = available_memos_df["الأستاذ"].unique().tolist()
                for p in profs_in_list:
                    p_clean = str(p).strip()
                    count = prof_counts.get(p_clean, 0)
                    if count < 4: available_profs.append(p_clean)
            available_profs = sorted(list(set(available_profs)))
            
            if available_profs:
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + available_profs)
                if selected_prof:
                    prof_specific_memos = available_memos_df[available_memos_df["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    if not prof_specific_memos.empty:
                        st.success(f'✅ لديك {len(prof_specific_memos)} خيار/خيارات متاحة:')
                        for _, row in prof_specific_memos.iterrows():
                            st.markdown(f"""
                            <div style="background: rgba(47, 111, 126, 0.15); border: 1px solid #2F6F7E; padding: 10px; border-radius: 8px; margin-bottom: 5px;">
                                <strong class="memo-card-title" style="color: #FFFFFF;">{row['رقم المذكرة']}</strong> - <span style="color: #FFFFFF;">{row['عنوان المذكرة']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else: st.info("هذا الأستاذ ليس لديه عناوين متاحة حالياً في تخصصك.")
            else:
                st.warning("🔒 عذراً، لا يوجد أساتذة لديهم أماكن شاغرة (أقل من 4 مذكرات) في تخصصك حالياً.")
                st.info("يرجى التواصل مع مسؤول الميدان أو المحاولة لاحقاً.")
            
            st.markdown("---")
            st.markdown("### ✍️ تسجيل المذكرة المختارة")
            c1, c2 = st.columns([3, 1])
            with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
            with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")
            
            if not st.session_state.show_confirmation:
                if st.button("المتابعة للتأكيد"):
                    if not st.session_state.note_number or not st.session_state.prof_password: 
                        st.error("⚠️ يرجى إدخال بيانات المذكرة")
                    elif registration_type == "ثنائية" and not student2_obj:
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني بشكل صحيح.")
                    elif s2_missing_info and (not s2_new_phone_val or not s2_new_nin_val):
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني الناقصة (هاتف و NIN).")
                    else:
                        s1_reg_perm = str(s1.get('التسجيل', '')).strip()
                        if registration_type == "ثنائية":
                            s2 = student2_obj
                            s2_reg_perm = str(s2.get('التسجيل', '')).strip()
                            if s1_reg_perm != '1' and s2_reg_perm != '1':
                                st.error("⛔ عذراً، لم يتم السماح لك بتسجيل المذكرة في الوقت الحالي."); st.stop()
                        else:
                            fardiya_val = str(s1.get('فردية', '')).strip()
                            if fardiya_val not in ["1", "نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                            if s1_reg_perm != '1': st.error("⛔ لم يتم السماح لك بتسجيل المذكرة في الوقت الحالي."); st.stop()

                        st.session_state.show_confirmation = True
                        st.session_state.s2_phone_input = s2_new_phone_val if s2_missing_info else ""
                        st.session_state.s2_nin_input = s2_new_nin_val if s2_missing_info else ""
                        st.rerun()
            else:
                st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("تأكيد نهائي", type="primary"):
                        valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                        if not valid: st.error(err); st.session_state.show_confirmation = False
                        else:
                            with st.spinner('⏳ جاري تسجيل...'):
                                s2_to_pass = student2_obj if registration_type == "ثنائية" else None
                                success, msg = update_registration(
                                    st.session_state.note_number, 
                                    s1, 
                                    s2_to_pass, 
                                    st.session_state.s2_phone_input, 
                                    st.session_state.s2_nin_input
                                )
                            if success: 
                                st.success(msg); st.balloons(); 
                                clear_cache_and_reload(); 
                                st.session_state.mode = "view"; 
                                st.session_state.show_confirmation = False; 
                                time.sleep(2); st.rerun()
                            else: st.error(msg); st.session_state.show_confirmation = False
                with col2:
                    if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

        elif st.session_state.mode == "view":
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("خروج", key="logout_btn"): logout()
            
            note_num = normalize_text(s1.get('رقم المذكرة', ''))
            df_memos_fresh = load_memos()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text) == note_num].iloc[0]

            tab_memo, tab_track, tab_notify = st.tabs(["مذكرتي", "تتبع ملف الشهادة", "الإشعارات والطلبات"])
            
            with tab_memo:
                session_date = memo_info.get("موعد الجلسة القادمة", "")
                session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date else ""
                st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;"><h3>✅ أنت مسجل في المذكرة التالية:</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {memo_info['الأستاذ']}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p>{session_html}</div>''', unsafe_allow_html=True)
                
                s1_lname, s1_fname = get_student_name_display(s1)
                s1_email = get_email_smart(s1)
                
                st.markdown("<h3>👥 معلومات الطلبة</h3>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="card">
                    <h4 style="color:#2F6F7E;">الطالب الأول</h4>
                    <p><b>اللقب:</b> {s1_lname}</p>
                    <p><b>الإسم:</b> {s1_fname}</p>
                    <p><b>رقم التسجيل:</b> {s1.get('رقم التسجيل')}</p>
                    <p><b>الإيميل:</b> {s1_email}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if s2:
                    s2_lname = s2.get("لقب", "")
                    s2_fname = s2.get("إسم", "")
                    s2_email = get_email_smart(s2)
                    st.markdown(f"""
                    <div class="card">
                        <h4 style="color:#2F6F7E;">الطالب الثاني</h4>
                        <p><b>اللقب:</b> {s2_lname}</p>
                        <p><b>الإسم:</b> {s2_fname}</p>
                        <p><b>رقم التسجيل:</b> {s2.get('رقم التسجيل')}</p>
                        <p><b>الإيميل:</b> {s2_email}</p>
                    </div>
                    """, unsafe_allow_html=True)

            with tab_track:
                st.subheader("📂 حالة ملف التخرج")
                def render_student_diploma_status(student_data, title):
                    if isinstance(student_data, dict):
                        cols = df_students.columns.tolist()
                        val_birth = student_data.get(cols[14]) if len(cols) > 14 else "غير محدد"
                        val_rel1 = student_data.get(cols[15]) if len(cols) > 15 else "غير محدد"
                        val_rel2 = student_data.get(cols[16]) if len(cols) > 16 else "غير محدد"
                        val_pv = student_data.get(cols[17]) if len(cols) > 17 else "غير محدد"
                        val_file = student_data.get(cols[18]) if len(cols) > 18 else "غير محدد"
                        val_dipl = student_data.get(cols[19]) if len(cols) > 19 else "غير محدد"
                    else:
                        vals = student_data.tolist()
                        val_birth = vals[14] if len(vals) > 14 else "غير محدد"
                        val_rel1 = vals[15] if len(vals) > 15 else "غير محدد"
                        val_rel2 = vals[16] if len(vals) > 16 else "غير محدد"
                        val_pv = vals[17] if len(vals) > 17 else "غير محدد"
                        val_file = vals[18] if len(vals) > 18 else "غير محدد"
                        val_dipl = vals[19] if len(vals) > 19 else "غير محدد"

                    def get_badge_color(val):
                        v = str(val).strip()
                        if v in ["متوفر", "مكتملة", "كامل", "كامل لحد الآن", "جاهز", "تم التسليم"]: return "status-available"
                        elif v in ["غير متوفر", "ناقص", "غير جاهز"]: return "status-unavailable"
                        else: return "status-pending"

                    html = f"""
                    <div class="card" style="border-right: 4px solid #2F6F7E;">
                        <h4 style="color:#FFD700; border-bottom:1px solid #444; padding-bottom:10px;">{title}</h4>
                        <div class="diploma-status-grid">
                            <div class="diploma-item"><span>📄 شهادة الميلاد</span><span class="status-badge {get_badge_color(val_birth)}">{val_birth}</span></div>
                            <div class="diploma-item"><span>📊 كشف نقاط (M1)</span><span class="status-badge {get_badge_color(val_rel1)}">{val_rel1}</span></div>
                            <div class="diploma-item"><span>📊 كشف نقاط (M2)</span><span class="status-badge {get_badge_color(val_rel2)}">{val_rel2}</span></div>
                            <div class="diploma-item"><span>📜 محضر المناقشة</span><span class="status-badge {get_badge_color(val_pv)}">{val_pv}</span></div>
                            <div class="diploma-item"><span>📂 حالة الملف</span><span class="status-badge {get_badge_color(val_file)}">{val_file}</span></div>
                            <div class="diploma-item"><span>🎓 حالة الشهادة</span><span class="status-badge {get_badge_color(val_dipl)}">{val_dipl}</span></div>
                        </div>
                    </div>
                    """
                    return html
                
                s1_lname, s1_fname = get_student_name_display(s1)
                st.markdown(render_student_diploma_status(s1, f"👤 {s1_lname} {s1_fname}"), unsafe_allow_html=True)
                st.info("ℹ️ ملاحظة: إذا كانت المذكرة ثنائية، سيظهر لك هنا فقط ملفك الشخصي. يتعين على الطالب الثاني الدخول بحسابه لمشاهدة ملفه.")

            with tab_notify:
                st.subheader("تنبيهات خاصة بك")
                df_reqs = load_requests()
                my_memo_id = note_num
                if my_memo_id:
                    df_memos_fresh = load_memos()
                    my_memo_row = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text) == my_memo_id]
                    if not my_memo_row.empty:
                        my_prof = str(my_memo_row.iloc[0]["الأستاذ"]).strip()
                        base_filter = df_reqs["النوع"] == "جلسة إشراف"
                        prof_filter = df_reqs["الأستاذ"].astype(str).str.strip() == my_prof
                        prof_sessions = df_reqs[base_filter & prof_filter]
                        if not prof_sessions.empty:
                            last_session = prof_sessions.iloc[-1]
                            details_display = ""; date_to_show = ""
                            try:
                                if len(last_session) > 8: 
                                    raw_val = last_session.iloc[8]
                                    if pd.notna(raw_val) and str(raw_val).strip() not in ['nan', '']:
                                        details_text = str(raw_val)
                                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', details_text)
                                        if date_match:
                                            raw_date_str = date_match.group(0)
                                            try:
                                                dt_obj = datetime.strptime(raw_date_str, '%Y-%m-%d')
                                                formatted_arabic_date = format_arabic_date(dt_obj)
                                                details_display = details_text.replace(raw_date_str, formatted_arabic_date)
                                                date_to_show = f"<p style='font-size:1.2rem; color:#FFD700; font-weight:bold; margin-top:10px;'>📅 {formatted_arabic_date}</p>"
                                            except: details_display = details_text
                                        else: details_display = details_text
                            except Exception: pass
                            st.markdown(f"""<div class='card' style='border-right: 4px solid #3B82F6; background: rgba(59, 130, 246, 0.1);'><h4>🔔 جلسة إشراف</h4>{date_to_show}<p>{details_display}</p></div>""", unsafe_allow_html=True)
                    
                    # Filter requests by memo number (normalized)
                    reqs_mask = df_reqs["رقم المذكرة"].astype(str).apply(normalize_text) == my_memo_id
                    my_reqs = df_reqs[reqs_mask]
                    if not my_reqs.empty:
                        for _, r in my_reqs.iterrows():
                            req_type = r['النوع']; details = ""
                            if len(r) > 8:
                                val = str(r.iloc[8]).strip()
                                if val and val.lower() not in ['nan', 'none']: details = val
                            show_details = True
                            if req_type in ["حذف طالب", "تنازل"]: show_details = False
                            st.markdown(f"""<div class="card" style="border-right: 4px solid #F59E0B; padding: 20px;"><h4>{req_type}</h4><p>الحالة: <b>{r.get('الحالة', 'غير محدد')}</b></p>{'<p>التفاصيل: ' + details + '</p>' if show_details and details else '<p><i>التفاصيل مخفية</i></p>'}</div>""", unsafe_allow_html=True)
                    if prof_sessions.empty and my_reqs.empty: st.info("لا توجد إشعارات جديدة.")
                else: st.info("يجب تسجيل مذكرة أولاً.")

# ============================================================
# فضاء الأساتذة
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_prof"): st.session_state.user_type = None; st.rerun()
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.query_params['ut'] = 'professor'; st.query_params['un'] = encode_str(normalize_text(r.get('إسم المستخدم', ''))); st.rerun()
    else:
        prof = st.session_state.professor; prof_name = prof["الأستاذ"]
        if st.session_state.get('selected_memo_id'):
            memo_id = st.session_state.selected_memo_id
            current_memo = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text) == memo_id].iloc[0]
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
                details_to_save = ""; validation_error = None
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_full_{memo_id}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_full_{memo_id}", use_container_width=True):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                elif req_op == "حذف طالب (ثنائية)":
                    if not student_info['s2_name']: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:"); st.write(f"1. {student_info['s1_name']}"); st.write(f"2. {student_info['s2_name']}")
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
                            df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
                            target = df_students[df_students["رقم التسجيل_norm"] == normalize_text(reg_to_add)]
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
                if validation_error: st.error(validation_error)
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
                            st.markdown(f'''<div class="card" style="border-right:5px solid #10B981; padding-bottom: 10px;"><h4>{memo['رقم المذكرة']} - {memo['عنوان المذكرة']}</h4><p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p><p style="font-size:0.95em; margin-bottom: 5px;">{s_info['s1_name']}</p>{f"<p style='font-size:0.95em; margin-bottom: 15px;'>{s_info['s2_name']}</p>" if s_info['s2_name'] else ""}<div class="progress-container" style="margin: 10px 0;"><div class="progress-bar" style="width: {prog_int}%;"></div></div><p style="text-align:left; font-size:0.8em;">نسبة الإنجاز: {prog_int}%</p></div>''', unsafe_allow_html=True)
                            if st.button(f"👉 عرض المذكرة {memo['رقم المذكرة']}", key=f"open_{memo['رقم المذكرة']}", use_container_width=True):
                                st.session_state.selected_memo_id = memo['رقم المذكرة']; st.rerun()
                else: st.info("لا توجد مذكرات مسجلة حتى الآن.")

            with tab2:
                st.subheader("📅 جدولة جلسة إشراف")
                st.info("سيتم إرسال الإشعار لكل الطلبة المسجلين لديك في المذكرات.")
                with st.form("supervision_session_form"):
                    c1, c2 = st.columns(2)
                    with c1: selected_date = st.date_input("تاريخ الجلسة", min_value=datetime.now().date())
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
                        if weekday in [4, 5]: st.error("❌ لا يمكن جدولة جلسات في يومي الجمعة والسبت.")
                        else:
                            session_datetime_str = format_datetime_ar(selected_date, selected_time)
                            details_text = f"موعد الجلسة: {session_datetime_str}"
                            target_students = get_students_of_professor(prof_name, df_memos)
                            if not target_students: st.warning("⚠️ لا يوجد طلاب مسجلون لديك حالياً لإرسال الإشعار.")
                            else:
                                save_success, save_msg = save_and_send_request("جلسة إشراف", prof_name, "جماعي", "جلسة إشراف", details_text, status="منجز")
                                if save_success:
                                    update_success, update_msg = update_session_date_in_sheets(prof_name, details_text)
                                    if update_success:
                                        st.success(f"✅ {save_msg}")
                                        st.info(f"تم تحديث موعد الجلسة في ملفات {len(target_students)} طالب.")
                                        email_success, email_msg = send_session_emails(target_students, details_text, prof_name)
                                        if email_success: st.success("📧 تم إرسال الإشعارات للطلبة والإدارة.")
                                        else: st.warning(f"⚠️ تم الحفظ لكن فاشل الإرسال: {email_msg}")
                                        time.sleep(2); st.rerun()
                                    else: st.error(f"تم حفظ الطلب ولكن حدث خطأ في تحديث المذكرات: {update_msg}")
                                else: st.error(save_msg)

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
                            st.markdown(f'''<div class="card" style="border-right:5px solid {color}; display:flex; justify-content:space-between; align-items:center;"><div><h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3><p style="margin:5px 0 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p></div></div>''', unsafe_allow_html=True)
                else: st.info("لا توجد كلمات سر مسندة إليك.")
            
            with tab4:
                if is_exhausted: st.subheader("💡 المذكرات المقترحة")
                else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
                avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
                if not avail.empty:
                    for _, m in avail.iterrows():
                        st.markdown(f'''<div class="card" style="border-left:4px solid #64748B;"><h4>{m['رقم المذكرة']}</h4><p>{m['عنوان المذكرة']}</p><p style="color:#94A3B8;">تخصص: {m['التخصص']}</p></div>''', unsafe_allow_html=True)
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
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.query_params['ut'] = 'admin'; st.query_params['un'] = encode_str(st.session_state.admin_user); st.rerun()
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
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B981;">{r_m}</div><div class="kpi-label">مذكرات مسجلة</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{a_m}</div><div class="kpi-label">مذكرات متاحة</div></div><div class="kpi-card" style="border-color: #10B981;"><div class="kpi-value" style="color: #10B98E;">{reg_st}</div><div class="kpi-label">طلاب مسجلين</div></div><div class="kpi-card" style="border-color: #F59E0B;"><div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div><div class="kpi-label">طلاب غير مسجلين</div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["المذكرات", "الطلاب", "الأساتذة", "تقارير", "تحديث", "إدارة الطلبات", "📧 إرسال إيميلات"])
        
        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل": d_memos = df_memos
            elif f_status == "مسجلة": d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else: d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            st.dataframe(d_memos, use_container_width=True, height=400)
        with tab2:
            st.subheader("قائمة الطلاب")
            q = st.text_input("بحث (لقب/اسم):")
            
            if st.session_state.get('admin_edit_student_user'):
                target_user = st.session_state.admin_edit_student_user
                student_data = df_students[df_students["اسم المستخدم"] == target_user]
                if not student_data.empty:
                    s = student_data.iloc[0]
                    vals = s.tolist()
                    
                    o_curr = vals[14] if len(vals) > 14 else ""
                    p_curr = vals[15] if len(vals) > 15 else ""
                    q_curr = vals[16] if len(vals) > 16 else ""
                    r_curr = vals[17] if len(vals) > 17 else ""
                    s_curr = vals[18] if len(vals) > 18 else ""
                    t_curr = vals[19] if len(vals) > 19 else ""

                    st.markdown(f"<h3>📝 تعديل ملف التخرج: {s.get('لقب', '')} {s.get('إسم', '')}</h3>", unsafe_allow_html=True)
                    
                    with st.form("edit_diploma_form"):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_o = st.selectbox("شهادة الميلاد", ["متوفر", "غير متوفر"], index=0 if o_curr=="متوفر" else 1)
                            new_p = st.selectbox("كشف1 (M1)", ["متوفر", "مدين", "محول", "خطأ في الكشف"], index=["متوفر", "مدين", "محول", "خطأ في الكشف"].index(p_curr) if p_curr in ["متوفر", "مدين", "محول", "خطأ في الكشف"] else 0)
                            new_q = st.selectbox("كشف2 (M2)", ["غير متوفر", "متوفر"], index=0 if q_curr=="غير متوفر" else 1)
                        with c2:
                            new_r = st.selectbox("محضر المناقشة", ["غير متوفر", "متوفر"], index=0 if r_curr=="غير متوفر" else 1)
                            new_s = st.selectbox("حالة الملف", ["ناقص", "كامل", "كامل لحد الآن"], index=["ناقص", "كامل", "كامل لحد الآن"].index(s_curr) if s_curr in ["ناقص", "كامل", "كامل لحد الآن"] else 0)
                            new_t = st.selectbox("حالة الشهادة", ["غير جاهز", "جاهز", "تم التسليم"], index=["غير جاهز", "جاهز", "تم التسليم"].index(t_curr) if t_curr in ["غير جاهز", "جاهز", "تم التسليم"] else 0)
                        
                        col_s, col_c = st.columns([1, 4])
                        with col_s:
                            save_btn = st.form_submit_button("💾 حفظ", use_container_width=True)
                            cancel_btn = st.form_submit_button("❌ إلغاء", use_container_width=True)
                        
                        if save_btn:
                            updates = {'O': new_o, 'P': new_p, 'Q': new_q, 'R': new_r, 'S': new_s, 'T': new_t}
                            success, msg = update_diploma_status(target_user, updates)
                            if success: 
                                st.success(msg)
                                st.session_state.admin_edit_student_user = None
                                st.rerun()
                            else: st.error(msg)
                        
                        if cancel_btn:
                            st.session_state.admin_edit_student_user = None
                            st.rerun()

            if q:
                name_cols = [c for c in df_students.columns if 'اسم' in c.lower() or 'لقب' in c.lower() or 'إسم' in c.lower()]
                if name_cols:
                    mask = df_students[name_cols].astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
                    f_st = df_students[mask]
                else: f_st = df_students
                
                for idx, row in f_st.iterrows():
                    u_name = row.get('اسم المستخدم')
                    full_name = f"{row.get('لقب', '')} {row.get('إسم', '')}"
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px; border:1px solid #333; display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                        <div>
                            <b style="color:#F8FAFC;">{full_name}</b><br>
                            <small style="color:#94A3B8;">{u_name} | {row.get('رقم التسجيل')}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    c_edit, c_space = st.columns([1, 4])
                    with c_edit:
                        if st.button("📝 ملف التخرج", key=f"edit_{idx}", use_container_width=True):
                            st.session_state.admin_edit_student_user = u_name
                            st.rerun()
            else: 
                st.dataframe(df_students, use_container_width=True, height=400)

        with tab3:
            st.subheader("توزيع الأساتذة")
            if df_memos.empty:
                st.warning("لا توجد بيانات مذكرات للعرض.")
            else:
                if "الأستاذ" not in df_memos.columns:
                    st.error("العمود 'الأستاذ' غير موجود في ملف المذكرات.")
                else:
                    profs_list = sorted(df_memos["الأستاذ"].dropna().unique().tolist())
                    sel_p = st.selectbox("اختر أستاذ:", ["الكل"] + profs_list)
                    
                    if sel_p != "الكل":
                        st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip() == sel_p.strip()], use_container_width=True, height=400)
                    else:
                        required_cols = ["الأستاذ", "رقم المذكرة", "تم التسجيل"]
                        missing_cols = [c for c in required_cols if c not in df_memos.columns]
                        
                        if not missing_cols:
                            s_df = df_memos.groupby("الأستاذ").agg(
                                total=("رقم المذكرة", "count"), 
                                registered=("تم التسجيل", lambda x: (x.astype(str).str.strip() == "نعم").sum())
                            ).reset_index()
                            s_df["المتاحة"] = s_df["total"] - s_df["registered"]
                            s_df = s_df.rename(columns={"total": "الإجمالي", "registered": "المسجلة"})
                            st.dataframe(s_df, use_container_width=True)
                        else:
                            st.error(f"بعض الأعمدة المطلوبة مفقودة: {', '.join(missing_cols)}")

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
        
        with tab7:
            st.subheader("إرسال رسالة ترحيب للأساتذة")
            send_mode = st.radio("اختر نوع العملية:", ["📩 إرسال لأستاذ محدد", "🚀 إرسال لجميع الأساتذة"], horizontal=True)
            st.markdown("---")
            if send_mode == "📩 إرسال لأستاذ محدد":
                st.info("أدخل بيانات الأستاذ لإرسال رسالة التفعيل له فقط.")
                prof_list = df_prof_memos["الأستاذ"].astype(str).dropna().unique().tolist()
                prof_list = list(set([p for p in prof_list if p.strip() and p.strip().lower() != "nan"]))
                prof_list.sort()
                selected_prof = st.selectbox("اختر الأستاذ من القائمة:", prof_list, index=None)
                col_s1, col_s2 = st.columns([1, 3])
                with col_s1:
                    send_single_btn = st.button("إرسال الآن", type="secondary", use_container_width=True)
                if send_single_btn and selected_prof:
                    success, msg = send_welcome_email_to_one(selected_prof)
                    if success: st.success(msg); st.balloons()
                    else: st.error(msg)
                elif send_single_btn and not selected_prof: st.warning("⚠️ يرجى اختيار اسم أستاذ من القائمة.")
            elif send_mode == "🚀 إرسال لجميع الأساتذة":
                st.info("تقوم هذه الأداة بإرسال إيميل يحتوي على بيانات الدخول لجميع الأساتذة.")
                st.write("عدد الأساتذة المستهدفين:", len(df_prof_memos))
                with st.expander("عرض قائمة الأساتذة المستهدفين"):
                     cols_available = df_prof_memos.columns.tolist()
                     target_cols = ["الأستاذ", "الأستاذة", "إسم المستخدم", "اسم المستخدم", "كلمة المرور", "البريد الإلكتروني", "الإيميل", "email", "Email"]
                     cols_to_display = [col for col in target_cols if col in cols_available]
                     if not cols_to_display: cols_to_display = cols_available[:3]
                     st.dataframe(df_prof_memos[cols_to_display].head(20))
                col_send, col_space = st.columns([1, 3])
                with col_send:
                    if st.button("🚀 بدء عملية الإرسال للجميع", type="primary"):
                        sent, failed, logs = send_welcome_emails_to_all_profs()
                        st.markdown("---")
                        st.success(f"تم الانتهاء! تم الإرسال بنجاح لـ {sent} أستاذ.")
                        if failed > 0: st.error(f"فشل الإرسال لـ {failed} أستاذ.")
                        with st.expander("سجل العمليات (Logs)", expanded=True):
                            for log in logs: st.text(log)

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;"> إشراف مسؤول الميدان البروفيسور لخضر رفاف © </div>', unsafe_allow_html=True)
