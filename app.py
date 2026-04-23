import streamlit as st
from datetime import datetime, time, date
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time as time_module
import textwrap
import base64
import re
from googleapiclient.http import MediaIoBaseUpload
import io
st.cache_data.clear()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(page_title="منصة مذكرات الماستر", page_icon="📘", layout="wide")

DEPOSIT_DEADLINE = datetime(2026, 5, 14, 23, 59)
REGISTRATION_DEADLINE = datetime(2027, 1, 28, 23, 59)

def get_days_remaining():
    delta = DEPOSIT_DEADLINE - datetime.now()
    return max(0, delta.days)

def render_countdown_banner():
    days = get_days_remaining()
    now = datetime.now()
    if now > DEPOSIT_DEADLINE:
        st.markdown("""<div style="background:linear-gradient(135deg,#1a472a,#2d6a4f);border-radius:16px;padding:16px 24px;margin-bottom:20px;display:flex;align-items:center;gap:14px;box-shadow:0 8px 24px rgba(45,106,79,0.3);"><span style="font-size:2rem;">✅</span><div><div style="color:#fff;font-size:1.05rem;font-weight:800;">انتهى أجل إيداع المذكرات</div><div style="color:rgba(255,255,255,0.9);font-size:0.82rem;">14 ماي 2026</div></div></div>""", unsafe_allow_html=True)
        return
    if days == 0:
        urgency = "⚡ اليوم الأخير للإيداع!"
        bg = "linear-gradient(135deg,#4A0000,#C0392B)"
        shadow = "rgba(192,57,43,0.6)"
    elif days <= 3:
        urgency = f"⚠️ تبقى {days} أيام فقط — أودع الآن!"
        bg = "linear-gradient(135deg,#7C0A02,#E74C3C)"
        shadow = "rgba(231,76,60,0.5)"
    elif days <= 7:
        urgency = f"📌 تبقى {days} أيام على آخر أجل"
        bg = "linear-gradient(135deg,#8B4513,#E67E22)"
        shadow = "rgba(230,126,34,0.4)"
    else:
        urgency = "📌 آخر أجل لإيداع المذكرات: 14 ماي 2026"
        bg = "linear-gradient(135deg,#1A3A5C,#2F6F7E)"
        shadow = "rgba(47,111,126,0.4)"
    st.markdown(f"""<div style="background:{bg};border-radius:16px;padding:16px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;box-shadow:0 8px 28px {shadow};"><div style="display:flex;align-items:center;gap:12px;"><span style="font-size:1.9rem;">⏳</span><div><div style="color:#fff;font-size:1.05rem;font-weight:800;">{urgency}</div><div style="color:rgba(255,255,255,0.9);font-size:0.8rem;margin-top:2px;">آخر أجل لإيداع المذكرات النهائية: 14 ماي 2026</div></div></div><div style="background:rgba(0,0,0,0.3);border:2px solid rgba(255,255,255,0.4);border-radius:12px;padding:8px 20px;text-align:center;"><div style="font-size:2.6rem;font-weight:900;color:#FFD700;line-height:1;text-shadow:0 0 20px rgba(255,215,0,0.5);">{days}</div><div style="font-size:0.72rem;color:rgba(255,255,255,0.8);letter-spacing:1px;">يوم متبقي</div></div></div>""", unsafe_allow_html=True)


st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: right; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 16px; margin:auto; }
h1, h2, h3, h4 { font-weight: 700; margin-bottom: 1rem; color: #ffffff !important; }
label, p, span { color: #ffffff !important; }
.stMarkdown div { color: #ffffff; }
.stMarkdown p { color: #ffffff !important; }
h1 { text-align: center; }
.stTextInput label, .stSelectbox label { color: #ffffff !important; font-weight: 600; }
    .stTextInput input, .stTextInput textarea { background-color: #ffffff !important; color: #1A2A3D !important; border: 1px solid #2F6F7E !important; border-radius: 8px !important; font-family: 'Cairo', sans-serif !important; font-size: 15px !important; }
    .stTextInput input::placeholder { color: #94A3B8 !important; }
    input[type="password"] { background-color: #ffffff !important; color: #1A2A3D !important; border: 1px solid #2F6F7E !important; border-radius: 8px !important; }
.stButton>button { background-color: #2F6F7E !important; color: #ffffff !important; font-size: 16px; font-weight: 600; padding: 14px 32px; border: none !important; border-radius: 12px !important; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: all 0.3s ease; width: 100%; text-align: center; }
.stButton>button:hover { background-color: #285E6B !important; transform: translateY(-2px); }
div[data-testid="stFormSubmitButton"] button { background-color: #2F6F7E !important; color: #ffffff !important; font-size: 16px; font-weight: 600; border: none !important; border-radius: 12px !important; width: 100%; }
div[data-testid="stFormSubmitButton"] button:hover { background-color: #285E6B !important; }
div[data-testid="stFormSubmitButton"] button p { color: #ffffff !important; }
.stButton>button p { color: #ffffff !important; }
.card { background: rgba(30,41,59,0.95); border:1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 30px; margin-bottom: 20px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); border-top: 3px solid #2F6F7E; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.2rem; margin-bottom: 2rem; }
.kpi-card { background: linear-gradient(145deg,#1E293B,#0F172A); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 2rem 1rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
.kpi-value { font-size: 2.2rem; font-weight: 900; color: #FFD700; margin: 10px 0; }
.kpi-label { font-size: 1rem; color: #ffffff !important; font-weight: 600; }
.alert-card { background: linear-gradient(90deg,#8B4513,#A0522D); border: 1px solid #CD853F; color: white; padding: 22px; border-radius: 12px; text-align: center; font-weight: bold; }
.progress-container { background-color: #0F172A; border-radius: 99px; padding: 5px; margin: 14px 0; overflow: hidden; }
.progress-bar { height: 22px; border-radius: 99px; background: linear-gradient(90deg,#2F6F7E,#285E6B,#FFD700); box-shadow: 0 0 15px rgba(47,111,126,0.5); }
.stDataFrame { border-radius: 12px; overflow: hidden; }
.stTabs [data-baseweb="tab-list"] { gap: 1.5rem; padding-bottom: 12px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #94A3B8; font-weight: 600; padding: 10px 20px; border-radius: 10px; border: 1px solid transparent; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.08); color: white; }
.stTabs [aria-selected="true"] { background: rgba(47,111,126,0.2); color: #FFD700; border: 1px solid #2F6F7E; font-weight: bold; }
.students-grid { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin: 20px 0; }
.student-card { flex:1; max-width:400px; min-width:260px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:22px; text-align:center; transition:all 0.3s; }
.student-card:hover { background:rgba(255,255,255,0.06); border-color:#2F6F7E; }
.diploma-item { background:rgba(255,255,255,0.04); padding:13px 17px; border-radius:10px; margin-bottom:9px; display:flex; justify-content:space-between; align-items:center; border-right:4px solid #2F6F7E; }
.status-badge { padding:4px 13px; border-radius:20px; font-size:0.86rem; font-weight:bold; min-width:88px; text-align:center; }
.status-available { background:rgba(16,185,129,0.15); color:#10B981; border:1px solid rgba(16,185,129,0.3); }
.status-unavailable { background:rgba(239,68,68,0.15); color:#EF4444; border:1px solid rgba(239,68,68,0.3); }
.status-pending { background:rgba(245,158,11,0.15); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
[data-testid="stFileUploader"] { background:rgba(15,41,66,0.9)!important; border:2px dashed #2F6F7E!important; border-radius:16px!important; padding:18px!important; }
[data-testid="stFileUploader"] label { color:#ffffff!important; font-weight:700!important; font-size:1rem!important; }
[data-testid="stFileUploaderDropzoneInstructions"] span,[data-testid="stFileUploaderDropzoneInstructions"] p,[data-testid="stFileUploaderDropzoneInstructions"] small { color:#E2E8F0!important; font-size:0.9rem!important; }
[data-testid="stFileUploaderDropzone"] { background:rgba(47,111,126,0.08)!important; border-radius:10px!important; }
[data-testid="stFileUploader"] button { background-color:#2F6F7E!important; color:#ffffff!important; border-radius:8px!important; border:none!important; font-weight:600!important; }
[data-testid="stFileUploader"] button:hover { background-color:#285E6B!important; }
[data-testid="stFileUploader"] button p { color:#ffffff!important; }
[data-testid="stFileUploader"] section { background:rgba(15,41,66,0.6)!important; border-radius:10px!important; }
[data-testid="stFileUploader"] section p, [data-testid="stFileUploader"] section span, [data-testid="stFileUploader"] section small { color:#E2E8F0!important; }
.deposit-hero { background:linear-gradient(135deg,#0F2942,#1A3A5C,#0F2942); border:2px solid #2F6F7E; border-radius:22px; padding:30px 34px; margin-bottom:22px; position:relative; overflow:hidden; }
.deposit-hero::before { content:''; position:absolute; top:-60px; left:-60px; width:240px; height:240px; background:radial-gradient(circle,rgba(47,111,126,0.16) 0%,transparent 70%); pointer-events:none; }
.deposit-hero-icon { font-size:3rem; display:block; margin-bottom:10px; }
.deposit-hero-title { font-size:1.5rem; font-weight:900; color:#FFD700!important; margin-bottom:7px; }
.deposit-hero-sub { font-size:0.92rem; color:#E2E8F0!important; line-height:1.6; }
.notif-card { border-radius:16px; padding:18px 22px; margin-bottom:14px; display:flex; gap:16px; align-items:flex-start; }
.notif-card-waiting { background:linear-gradient(135deg,rgba(245,158,11,0.1),rgba(245,158,11,0.04)); border:1.5px solid rgba(245,158,11,0.42); }
.notif-card-approved { background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(16,185,129,0.04)); border:1.5px solid rgba(16,185,129,0.42); }
.notif-card-rejected { background:linear-gradient(135deg,rgba(239,68,68,0.1),rgba(239,68,68,0.04)); border:1.5px solid rgba(239,68,68,0.42); }
.notif-card-scheduled { background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(99,102,241,0.04)); border:1.5px solid rgba(99,102,241,0.42); }
.notif-icon { font-size:1.9rem; flex-shrink:0; margin-top:2px; }
.notif-title { font-size:1.02rem; font-weight:700; margin-bottom:5px; }
.notif-title-waiting { color:#F59E0B!important; } .notif-title-approved { color:#10B981!important; }
.notif-title-rejected { color:#EF4444!important; } .notif-title-scheduled { color:#818CF8!important; }
.notif-desc { color:#ffffff!important; font-size:0.86rem; line-height:1.7; }
.defense-schedule-card { background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(99,102,241,0.04)); border:2px solid rgba(99,102,241,0.38); border-radius:18px; padding:24px; margin:18px 0; }
.defense-info-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-top:12px; }
.defense-info-item { background:rgba(255,255,255,0.05); border-radius:10px; padding:13px; text-align:center; }
.defense-info-label { font-size:0.73rem; color:#E2E8F0!important; margin-bottom:4px; }
.defense-info-value { font-size:1.05rem; font-weight:700; color:#818CF8!important; }
.jury-card { background:linear-gradient(145deg,#0F1E30,#162840); border:1px solid rgba(255,255,255,0.07); border-radius:18px; padding:24px; margin:18px 0; }
.jury-header { background:linear-gradient(135deg,#1E3A5F,#2F6F7E); border-radius:11px; padding:14px 18px; margin-bottom:20px; display:flex; align-items:center; gap:12px; }
.jury-header-icon { font-size:1.8rem; }
.jury-header-title { font-size:1rem; font-weight:700; color:#FFD700!important; margin:0; }
.jury-header-sub { font-size:0.8rem; color:rgba(255,255,255,0.85)!important; margin:0; }
.jury-members-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:13px; margin-bottom:16px; }
.jury-member-card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07); border-radius:13px; padding:16px; text-align:center; transition:all 0.3s; }
.jury-member-card:hover { background:rgba(255,255,255,0.07); border-color:rgba(47,111,126,0.38); transform:translateY(-2px); }
.jury-member-avatar { width:48px; height:48px; border-radius:50%; margin:0 auto 9px; display:flex; align-items:center; justify-content:center; font-size:1.25rem; }
.avatar-president { background:rgba(255,215,0,0.1); border:2px solid rgba(255,215,0,0.38); }
.avatar-supervisor { background:rgba(47,111,126,0.16); border:2px solid rgba(47,111,126,0.38); }
.avatar-examiner { background:rgba(148,163,184,0.08); border:2px solid rgba(148,163,184,0.18); }
.jury-member-role { font-size:0.7rem; font-weight:700; letter-spacing:0.7px; padding:3px 9px; border-radius:20px; display:inline-block; margin-bottom:7px; }
.role-president { background:rgba(255,215,0,0.1); color:#FFD700!important; border:1px solid rgba(255,215,0,0.28); }
.role-supervisor { background:rgba(47,111,126,0.14); color:#2F9EA0!important; border:1px solid rgba(47,111,126,0.28); }
.role-examiner { background:rgba(148,163,184,0.08); color:#E2E8F0!important; border:1px solid rgba(148,163,184,0.18); }
.jury-member-name { font-size:0.9rem; font-weight:700; color:#ffffff!important; line-height:1.4; }
.prof-deposit-alert { background:linear-gradient(135deg,#0D2010,#0F2020); border:2px solid rgba(16,185,129,0.42); border-radius:18px; margin-bottom:22px; overflow:hidden; box-shadow:0 8px 28px rgba(16,185,129,0.1); }
.prof-deposit-alert-header { background:linear-gradient(135deg,rgba(16,185,129,0.17),rgba(16,185,129,0.04)); padding:17px 21px; display:flex; align-items:center; gap:13px; border-bottom:1px solid rgba(16,185,129,0.17); }
.prof-deposit-alert-icon { font-size:1.9rem; }
.prof-deposit-alert-title { font-size:1.1rem; font-weight:800; color:#10B981!important; margin:0; }
.prof-deposit-alert-sub { font-size:0.8rem; color:#ffffff!important; margin:0; }
.prof-deposit-list { padding:13px 19px; }
.prof-deposit-item { background:rgba(255,255,255,0.03); border:1px solid rgba(16,185,129,0.17); border-radius:11px; padding:13px 17px; margin-bottom:9px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:7px; transition:background 0.2s; }
.prof-deposit-item:hover { background:rgba(16,185,129,0.07); }
.prof-deposit-memo-num { font-size:1.2rem; font-weight:900; color:#FFD700!important; }
.prof-deposit-memo-title { font-size:0.86rem; color:#E2E8F0!important; margin-top:2px; }
.prof-deposit-memo-date { font-size:0.76rem; color:#E2E8F0!important; margin-top:3px; }
.declaration-card { background:linear-gradient(145deg,#0A1628,#0F1E30); border:1px solid rgba(255,255,255,0.08); border-radius:20px; overflow:hidden; margin:17px 0; }
.declaration-card-header { background:linear-gradient(135deg,#1E3A5F,#0F2942); padding:19px 24px; border-bottom:1px solid rgba(255,255,255,0.07); }
.declaration-card-title { font-size:1.15rem; font-weight:800; color:#FFD700!important; margin:0 0 3px; }
.declaration-card-sub { font-size:0.8rem; color:rgba(255,255,255,0.8)!important; margin:0; }
.declaration-card-body { padding:22px 24px; }
.declaration-step-label { font-size:0.8rem; font-weight:600; color:#ffffff!important; margin-bottom:7px; letter-spacing:0.3px; }
.declaration-preview { background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-right:4px solid #2F6F7E; border-radius:9px; padding:13px 15px; font-size:0.85rem; color:#ffffff!important; line-height:1.9; font-style:italic; }
.declaration-preview strong { color:#FFD700!important; font-style:normal; }
</style>
""", unsafe_allow_html=True)


SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES_DRIVE  = ['https://www.googleapis.com/auth/drive']

try:
    info = st.secrets["service_account"]
    credentials = Credentials.from_service_account_info(info, scopes=SCOPES_SHEETS)
    sheets_service = build('sheets', 'v4', credentials=credentials)
except Exception as e:
    st.error("⚠️ خطأ في الاتصال بـ Google Sheets"); st.stop()

DRIVE_UPLOAD_FOLDER_ID = "1fvckcOGegVD4Ofs-UnVZbVCbYBQlToWs"
try:
    drive_info = st.secrets["drive_service_account"]
    drive_credentials = Credentials.from_service_account_info(drive_info, scopes=SCOPES_DRIVE)
    drive_service = build('drive', 'v3', credentials=drive_credentials)
except:
    drive_service = None

STUDENTS_SHEET_ID   = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID      = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"
REQUESTS_SHEET_ID   = "1sTJ6BZRM4Qgt0w2xUkpFZqquL-hfriMYTSN3x1_12_o"
STUDENTS_RANGE  = "Feuille 1!A1:U1000"
MEMOS_RANGE     = "Feuille 1!A1:AI1000"
PROF_MEMOS_RANGE= "Feuille 1!A1:P1000"
REQUESTS_RANGE  = "Feuille 1!A1:K1000"
ADMIN_CREDENTIALS = {"admin": "admin2026", "dsp": "dsp@2026"}
EMAIL_SENDER  = "domaine.dsp@univ-bba.dz"
EMAIL_PASSWORD= "oqwejylusjllfvhc"
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
ADMIN_EMAIL   = "domaine.dsp@univ-bba.dz"

def format_arabic_date(date_input):
    try:
        if isinstance(date_input, str): date_obj = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
        elif isinstance(date_input, datetime): date_obj = date_input
        else: return str(date_input)
        months_map = {1:"جانفي",2:"فيفري",3:"مارس",4:"أفريل",5:"ماي",6:"جوان",7:"جويلية",8:"أوت",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}
        return f"{date_obj.day:02d} {months_map.get(date_obj.month,'')} {date_obj.year}"
    except: return str(date_input)

def col_letter(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n-1, 26)
        result = chr(65+remainder) + result
    return result

def sanitize_input(text):
    if not text: return ""
    cleaned = str(text).strip()
    for c in ['<','>','"',"'",'&','|','`']: cleaned = cleaned.replace(c,'')
    return cleaned

def normalize_text(val):
    v = str(val).strip()
    if v.endswith('.0'): v = v[:-2]
    return v

def validate_username(u):
    u = sanitize_input(u)
    if not u: return False, "⚠️ فارغ"
    return True, u

def validate_note_number(n):
    n = sanitize_input(n)
    if not n: return False, "⚠️ فارغ"
    if len(n)>20: return False, "⚠️ غير صالح"
    return True, n

def is_phone_valid(phone_val):
    val = str(phone_val).strip()
    if val in ['','0','-','nan','None','NaN','.0','0.0']: return False, "فارغ"
    cleaned = val.replace(' ','').replace('-','')
    if not cleaned.isdigit(): return False, "ليس أرقام"
    if len(cleaned) < 9: return False, "قصير"
    return True, "صالح"

def is_nin_valid(nin_val):
    val = str(nin_val).strip().replace('.0','')
    if val in ['','0','-','nan','None','NaN']: return False, "فارغ"
    if not val.isdigit(): return False, "ليس أرقام"
    return True, "صالح"

def get_student_name_display(student_dict):
    lname = ""
    for k in ["اللقب","لقب","Nom","nom"]:
        val = str(student_dict.get(k,"")).strip()
        if val and val not in ['nan','None','-']: lname = val; break
    fname = ""
    for k in ["الإسم","إسم","اسم","الاسم","Prénom","prenom"]:
        val = str(student_dict.get(k,"")).strip()
        if val and val not in ['nan','None','-']: fname = val; break
    return lname, fname

def get_email_smart(row):
    if isinstance(row, dict):
        priority_keys = ["الإيميل", "البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]
        for key in priority_keys:
            val = str(row.get(key, "")).strip()
            if "@" in val and val != "nan": return val
        for val in row.values():
            v = str(val).strip()
            if "@" in v and v != "nan": return v
        return ""
    try:
        # البحث في المواضع 9 إلى 12 (كما في الكود الأصلي)
        values_list = row.tolist()
        for i in range(9, 13):
            if i < len(values_list):
                val = str(values_list[i]).strip()
                if "@" in val and val != "nan": return val
        # البحث بالاسم
        for col in row.index:
            clean_col = str(col).strip()
            if clean_col in ["الإيميل", "البريد المهني", "البريد الإلكتروني", "email", "Email", "E-mail"]:
                val = str(row[col]).strip()
                if "@" in val and val != "nan": return val
        return ""
    except:
        return ""

def load_student2_for_memo(memo_row, current_student_reg, df_students):
    memo_list = memo_row.tolist() if hasattr(memo_row,'tolist') else list(memo_row.values())
    reg_s = normalize_text(memo_row.get("رقم تسجيل الطالب 1", memo_list[18] if len(memo_list)>18 else ""))
    reg_t = normalize_text(memo_row.get("رقم تسجيل الطالب 2", memo_list[19] if len(memo_list)>19 else ""))
    current_reg = normalize_text(current_student_reg)
    other_reg = reg_t if current_reg == reg_s else (reg_s if current_reg == reg_t else reg_t)
    if not other_reg or other_reg in ["","nan"]: return None
    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
    s2 = df_students[df_students["رقم التسجيل_norm"] == other_reg]
    return s2.iloc[0].to_dict() if not s2.empty else None

def get_student_info_from_memo(memo_row, df_students):
    s1_name = str(memo_row.get("الطالب الأول","")).strip()
    s2_name = str(memo_row.get("الطالب الثاني","")).strip()
    s1_email = s2_email = s1_reg = s2_reg = ""
    try:
        memo_list = memo_row.tolist()
        reg1 = normalize_text(str(memo_list[18]).strip() if len(memo_list)>18 else "")
        reg2 = normalize_text(str(memo_list[19]).strip() if len(memo_list)>19 else "")
    except:
        reg1 = normalize_text(memo_row.get("رقم تسجيل الطالب 1",""))
        reg2 = normalize_text(memo_row.get("رقم تسجيل الطالب 2",""))
    df_students['رقم التسجيل_norm'] = df_students['رقم التسجيل'].astype(str).apply(normalize_text)
    if reg1:
        s = df_students[df_students["رقم التسجيل_norm"]==reg1]
        if not s.empty: s1_email = get_email_smart(s.iloc[0]); s1_reg = reg1
    if s2_name and reg2:
        s = df_students[df_students["رقم التسجيل_norm"]==reg2]
        if not s.empty: s2_email = get_email_smart(s.iloc[0]); s2_reg = reg2
    return {"s1_name":s1_name,"s1_email":s1_email,"s1_reg":s1_reg,"s2_name":s2_name,"s2_email":s2_email,"s2_reg":s2_reg}

@st.cache_data(ttl=60)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
        values = result.get('values',[])
        if not values: return pd.DataFrame()
        df = pd.DataFrame(values[1:], columns=values[0]); df.columns = df.columns.str.strip(); return df
    except Exception as e: logger.error(f"خطأ الطلاب: {e}"); return pd.DataFrame()

@st.cache_data(ttl=60)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range="Feuille 1!A1:AI1000").execute()
        values = result.get('values',[])
        if not values: return pd.DataFrame()
        headers = values[0]; rows = values[1:]
        padded = [r+['']*(len(headers)-len(r)) for r in rows]
        return pd.DataFrame(padded, columns=headers)
    except Exception as e: logger.error(f"خطأ المذكرات: {e}"); return pd.DataFrame()

@st.cache_data(ttl=60)
def load_prof_memos():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
        values = result.get('values',[])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e: logger.error(f"خطأ الأساتذة: {e}"); return pd.DataFrame()

@st.cache_data(ttl=60)
def load_requests():
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=REQUESTS_SHEET_ID, range=REQUESTS_RANGE).execute()
        values = result.get('values',[])
        if not values: return pd.DataFrame()
        return pd.DataFrame(values[1:], columns=values[0])
    except: return pd.DataFrame()

def clear_cache_and_reload(): st.cache_data.clear()


def _email_style():
    return """<style>body{font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;direction:rtl;text-align:right;}.container{background:#fff;padding:28px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.1);max-width:600px;margin:auto;}.header{background:linear-gradient(135deg,#0F2942,#2F6F7E);color:#fff;padding:20px;border-radius:8px;text-align:center;margin-bottom:18px;}.header h2{margin:0;font-size:1.3rem;}.info-box{background:#f0f9ff;padding:14px;border-right:4px solid #2F6F7E;margin:12px 0;border-radius:6px;}.action-box{background:#fff8e1;padding:14px;border-right:4px solid #F59E0B;margin:12px 0;border-radius:6px;}.success-box{background:#f0fdf4;padding:14px;border-right:4px solid #10B981;margin:12px 0;border-radius:6px;}.warning-box{background:#fff1f2;padding:14px;border-right:4px solid #EF4444;margin:12px 0;border-radius:6px;}.reject-box{background:#fff1f2;padding:14px;border-right:4px solid #EF4444;margin:12px 0;border-radius:6px;}.platform-btn{display:inline-block;background:#2F6F7E;color:#fff!important;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:10px;}.footer{text-align:center;color:#888;font-size:12px;margin-top:24px;border-top:1px solid #eee;padding-top:12px;}p{color:#333;line-height:1.8;}</style>"""

def send_deposit_email_to_professor(prof_name, memo_number, memo_title, student1_name, student2_name=None):
    try:
        df_profs = load_prof_memos()
        # البحث بـ اسم الأستاذ + رقم المذكرة
        prof_rows = df_profs[
            (df_profs["الأستاذ"].astype(str).str.strip()==prof_name.strip()) &
            (df_profs["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number))
        ]
        # إن لم يُوجد بالرقم، نبحث بالاسم فقط ونأخذ الصف الذي فيه إيميل
        if prof_rows.empty:
            all_prof_rows = df_profs[df_profs["الأستاذ"].astype(str).str.strip()==prof_name.strip()]
            prof_rows = all_prof_rows
        if prof_rows.empty: return False, f"الأستاذ غير موجود في قاعدة البيانات: {prof_name}"
        # البحث في كل صفوف الأستاذ حتى نجد إيميلاً
        prof_email = ""
        for _, prow in prof_rows.iterrows():
            email_candidate = get_email_smart(prow)
            if email_candidate and "@" in email_candidate:
                prof_email = email_candidate
                break
        if not prof_email: return False, f"البريد غير متوفر للأستاذ: {prof_name}"
        students_html = f"<p>👤 <strong>الطالب الأول:</strong> {student1_name}</p>"
        if student2_name and student2_name.strip() and student2_name != student1_name:
            students_html += f"<p>👤 <strong>الطالب الثاني:</strong> {student2_name}</p>"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        body = f"""<html dir="rtl"><head><meta charset="UTF-8">{_email_style()}</head><body><div class="container"><div class="header"><h2>📥 إيداع مذكرة — للإطلاع والمراجعة</h2><p style="color:rgba(255,255,255,0.8);margin:5px 0 0;font-size:0.88rem;">جامعة محمد البشير الإبراهيمي — كلية الحقوق</p></div><p>الأستاذ(ة) الفاضل(ة) <strong>{prof_name}</strong>،</p><p>نحيطكم علماً بأن الطالب(ين) أودعوا نسختهم النهائية من المذكرة رقم <strong>{memo_number}</strong> عبر منصة مذكرات الماستر بتاريخ <strong>{timestamp}</strong>.</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p><p>📑 <strong>العنوان:</strong> {memo_title}</p>{students_html}</div><div class="action-box"><p>يُرجى الدخول إلى المنصة للاطلاع على المذكرة المودعة، ثم اتخاذ قرار الموافقة أو الإعادة مع الملاحظات.</p></div><div style="text-align:center;margin:20px 0;"><a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 الدخول إلى منصة المذكرات</a></div><div class="footer"><p>مسؤول الميدان: البروفيسور لخضر رفاف</p><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
        for recipient in [prof_email, ADMIN_EMAIL]:
            msg = MIMEMultipart('alternative')
            msg['From']=EMAIL_SENDER; msg['To']=recipient
            msg['Subject']=f"📥 إيداع مذكرة للمراجعة — رقم {memo_number}"
            msg.attach(MIMEText(body,'html','utf-8'))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال الإشعار"
    except Exception as e: return False, f"❌ {str(e)}"

def send_approval_email_to_students(memo_number, memo_title, prof_name, student1_data, student2_data=None):
    try:
        recipients = []; names = []
        for s in [student1_data, student2_data]:
            if s is None: continue
            e = get_email_smart(s)
            if e: recipients.append(e)
            ln, fn = get_student_name_display(s); names.append(f"{ln} {fn}".strip())
        if not recipients: return False, "لا يوجد بريد"
        names_str = " و ".join(names)
        body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header"><h2>🟢 مذكرتك معتمدة — قابلة للمناقشة</h2></div><p>تحية طيبة، {names_str}،</p><p>يسعدنا إعلامكم بأن الأستاذ المشرف <strong>{prof_name}</strong> وافق على مذكرتكم رسمياً.</p><div class="success-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p><p>📑 <strong>العنوان:</strong> {memo_title}</p><p>✅ <strong>الحالة:</strong> قابلة للمناقشة</p></div><p>ستتلقون إشعاراً من الإدارة بموعد ومكان المناقشة.</p><div style="text-align:center;margin:16px 0;"><a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 متابعة على المنصة</a></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=recipients[0]
        if len(recipients)>1: msg['Cc']=", ".join(recipients[1:])
        msg['Bcc']=ADMIN_EMAIL
        msg['Subject']=f"🟢 مذكرتك معتمدة — رقم {memo_number}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال إشعار الموافقة"
    except Exception as e: return False, f"❌ {str(e)}"

def send_rejection_email_to_students(memo_number, memo_title, prof_name, reason, s1_data, s2_data=None):
    try:
        recipients = []; names = []
        for s in [s1_data, s2_data]:
            if s is None: continue
            e = get_email_smart(s)
            if e: recipients.append(e)
            ln, fn = get_student_name_display(s); names.append(f"{ln} {fn}".strip())
        if not recipients: return False, "لا يوجد بريد"
        names_str = " و ".join(names)
        body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header" style="background:linear-gradient(135deg,#450a0a,#EF4444);"><h2>🔴 المذكرة بحاجة لمراجعة</h2></div><p>تحية طيبة، {names_str}،</p><p>أعاد الأستاذ المشرف <strong>{prof_name}</strong> مذكرتكم للمراجعة.</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p><p>📑 <strong>العنوان:</strong> {memo_title}</p></div><div class="reject-box"><p><strong>📋 ملاحظات المشرف وسبب الإعادة:</strong></p><p style="font-style:italic;color:#C0392B;">{reason}</p></div><div class="action-box"><p>⚠️ يُرجى مراجعة الملاحظات وإعادة رفع النسخة المُصححة عبر المنصة.</p></div><div style="text-align:center;margin:16px 0;"><a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 الدخول للمنصة</a></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=recipients[0]
        if len(recipients)>1: msg['Cc']=", ".join(recipients[1:])
        msg['Bcc']=ADMIN_EMAIL
        msg['Subject']=f"🔴 ملاحظات على مذكرتك — رقم {memo_number}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال إشعار الإعادة"
    except Exception as e: return False, f"❌ {str(e)}"

def send_notes_email_to_students(memo_number, memo_title, prof_name, notes, s1_data, s2_data=None):
    try:
        recipients = []; names = []
        for s in [s1_data, s2_data]:
            if s is None: continue
            e = get_email_smart(s)
            if e: recipients.append(e)
            ln, fn = get_student_name_display(s); names.append(f"{ln} {fn}".strip())
        if not recipients: return False, "لا يوجد بريد"
        names_str = " و ".join(names)
        body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header" style="background:linear-gradient(135deg,#1e1b4b,#6366F1);"><h2>📝 ملاحظات المشرف</h2></div><p>تحية طيبة، {names_str}،</p><p>أرسل الأستاذ المشرف <strong>{prof_name}</strong> ملاحظاته على مذكرتكم رقم <strong>{memo_number}</strong>.</p><div style="background:#f0f0ff;padding:14px;border-right:4px solid #6366F1;margin:12px 0;border-radius:6px;"><p><strong>💬 الملاحظات:</strong></p><p style="font-style:italic;color:#4338CA;">{notes}</p></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=recipients[0]
        if len(recipients)>1: msg['Cc']=", ".join(recipients[1:])
        msg['Subject']=f"📝 ملاحظات المشرف — رقم {memo_number}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال الملاحظات"
    except Exception as e: return False, f"❌ {str(e)}"

def send_defense_schedule_email(memo_number, memo_title, prof_name, defense_date, defense_time, defense_room, s1_data, s2_data=None):
    try:
        recipients = []; names = []
        for s in [s1_data, s2_data]:
            if s is None: continue
            e = get_email_smart(s)
            if e: recipients.append(e)
            ln, fn = get_student_name_display(s); names.append(f"{ln} {fn}".strip())
        if not recipients: return False, "لا يوجد بريد"
        names_str = " و ".join(names)
        body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header"><h2>📅 موعد مناقشة مذكرتك</h2></div><p>تحية طيبة، {names_str}،</p><p>تم تحديد موعد مناقشتكم رسمياً.</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_number}</p><p>📑 <strong>العنوان:</strong> {memo_title}</p><p>👨‍🏫 <strong>المشرف:</strong> {prof_name}</p></div><div class="success-box"><p>📆 <strong>التاريخ:</strong> <span style="font-size:1.05rem;color:#10B981;">{defense_date}</span></p><p>🕐 <strong>التوقيت:</strong> <span style="font-size:1.05rem;color:#10B981;">{defense_time}</span></p><p>🏛️ <strong>القاعة:</strong> <span style="font-size:1.05rem;color:#10B981;">{defense_room}</span></p></div><div class="warning-box"><p>⚠️ يرجى الحضور قبل الموعد بـ 15 دقيقة مع جميع الوثائق.</p></div><div style="text-align:center;margin:16px 0;"><a href="https://memoires2026.streamlit.app" class="platform-btn">🔗 متابعة على المنصة</a></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=recipients[0]
        if len(recipients)>1: msg['Cc']=", ".join(recipients[1:])
        msg['Bcc']=ADMIN_EMAIL
        msg['Subject']=f"📅 موعد مناقشتك — رقم {memo_number}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "✅ تم إرسال موعد المناقشة"
    except Exception as e: return False, f"❌ {str(e)}"

def _send_email_to_professor_row(row):
    prof_name = row.get("الأستاذ","")
    email = ""; username = ""; password = ""
    for col in ["البريد الإلكتروني","الإيميل","email","Email","E-mail"]:
        if col in row.index:
            val = str(row[col]).strip()
            if "@" in val and val != "nan": email = val; break
    for col in ["إسم المستخدم","اسم المستخدم","Identifiant"]:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val: username = val; break
    for col in ["كلمة المرور","كلمة السر","Password"]:
        if col in row.index:
            val = str(row[col]).strip()
            if val != "nan" and val: password = val; break
    if not email or not username or not password: return False, "⚠️ بيانات ناقصة"
    body = f"""<html dir="rtl"><head><style>body{{font-family:Arial,sans-serif;direction:rtl;background:#f4f4f4;padding:20px;}}.container{{background:#fff;padding:28px;border-radius:12px;max-width:600px;margin:auto;}}.header{{background:linear-gradient(135deg,#003366,#005580);color:white;padding:18px;border-radius:8px;text-align:center;margin-bottom:18px;}}.info-box{{background:#eef7fb;border-right:5px solid #005580;padding:18px;margin:14px 0;border-radius:4px;}}.footer{{text-align:center;color:#666;font-size:12px;margin-top:24px;border-top:1px solid #eee;padding-top:14px;}}p{{color:#333;line-height:1.7;}}</style></head><body><div class="container"><div class="header"><h2>جامعة محمد البشير الإبراهيمي</h2><h3>كلية الحقوق والعلوم السياسية</h3></div><p>تحية طيبة، الأستاذ(ة) <strong>{prof_name}</strong>،</p><p>تم تفعيل فضاء الأساتذة على منصة متابعة مذكرات الماستر.</p><div class="info-box"><p>🔗 <a href="https://memoires2026.streamlit.app">https://memoires2026.streamlit.app</a></p><p>👤 <strong>اسم المستخدم:</strong> {username}</p><p>🔑 <strong>كلمة المرور:</strong> {password}</p></div><div class="footer"><p>مسؤول الميدان: البروفيسور لخضر رفاف</p></div></div></body></html>"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=email
        msg['Subject']="تفعيل حساب فضاء الأساتذة - منصة المذكرات"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, f"✅ تم الإرسال إلى {email}"
    except Exception as e: return False, f"❌ {str(e)}"

def send_welcome_emails_to_all_profs():
    df_profs = load_prof_memos(); sent=0; failed=0; logs=[]
    pb = st.progress(0); total = len(df_profs)
    with st.spinner("⏳ جاري الإرسال..."):
        for i,(_,row) in enumerate(df_profs.iterrows()):
            ok,msg = _send_email_to_professor_row(row)
            if ok: sent+=1
            else: failed+=1
            logs.append(msg); pb.progress((i+1)/total); time_module.sleep(0.5)
    return sent, failed, logs

def send_welcome_email_to_one(prof_name):
    df_profs = load_prof_memos()
    rows = df_profs[df_profs["الأستاذ"].astype(str).str.strip()==prof_name.strip()]
    if rows.empty: return False, f"❌ لم يتم العثور على: {prof_name}"
    return _send_email_to_professor_row(rows.iloc[0])

def send_email_to_professor(prof_name, memo_info, student1, student2=None):
    df_profs = load_prof_memos()
    prof_row = df_profs[df_profs["الأستاذ"].astype(str).str.strip()==prof_name.strip()]
    if prof_row.empty: return False, "لم يُعثر على الأستاذ"
    prof_email = get_email_smart(prof_row.iloc[0])
    if "@" not in prof_email: return False, "البريد فارغ"
    s1_ln,s1_fn = get_student_name_display(student1)
    s2_info = ""
    if student2:
        s2_ln,s2_fn = get_student_name_display(student2)
        s2_info = f"<p>👤 <strong>الطالب الثاني:</strong> {s2_ln} {s2_fn}</p>"
    body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header"><h2>✅ تسجيل مذكرة جديدة</h2></div><p>الأستاذ(ة) <strong>{prof_name}</strong>،</p><div class="info-box"><p>📄 <strong>رقم المذكرة:</strong> {memo_info['رقم المذكرة']}</p><p>📑 <strong>العنوان:</strong> {memo_info['عنوان المذكرة']}</p><p>🎓 <strong>التخصص:</strong> {memo_info['التخصص']}</p><p>👤 <strong>الطالب الأول:</strong> {s1_ln} {s1_fn}</p>{s2_info}<p>🕒 <strong>تاريخ التسجيل:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=prof_email
        msg['Subject']=f"✅ تسجيل مذكرة رقم {memo_info['رقم المذكرة']}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "تم الإرسال"
    except Exception as e: return False, f"❌ {str(e)}"

def send_session_emails(students_data, session_info, prof_name):
    df_s = load_students(); df_s['رقم التسجيل_norm'] = df_s['رقم التسجيل'].astype(str).apply(normalize_text)
    emails = []
    for s in students_data:
        row = df_s[df_s["رقم التسجيل_norm"]==s['reg']]
        if not row.empty:
            e = get_email_smart(row.iloc[0])
            if e: emails.append(e)
    body = f"""<html dir="rtl"><head>{_email_style()}</head><body><div class="container"><div class="header"><h2>📅 جلسة إشراف</h2></div><p>الأستاذ(ة) <strong>{prof_name}</strong> يُعلن عن جلسة إشراف:</p><div class="success-box"><p><strong>📆 الموعد:</strong> {session_info}</p></div><div class="footer"><p>جامعة محمد البشير الإبراهيمي</p></div></div></body></html>"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From']=EMAIL_SENDER; msg['To']=ADMIN_EMAIL
        if emails: msg['Bcc']=", ".join(emails)
        msg['Subject']=f"🔔 جلسة إشراف — {prof_name}"
        msg.attach(MIMEText(body,'html','utf-8'))
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD); server.send_message(msg)
        return True, "تم"
    except Exception as e: return False, str(e)


def upload_memo_to_drive(pdf_bytes, memo_number, memo_title):
    if drive_service is None: return False, "", "❌ Drive غير متاح"
    try:
        safe_title = re.sub(r'[\\/:*?"<>|]','',str(memo_title).strip())
        file_name = f"{memo_number}.{safe_title}.pdf"
        existing = drive_service.files().list(q=f"'{DRIVE_UPLOAD_FOLDER_ID}' in parents and name contains '{memo_number}.' and trashed=false", fields="files(id)").execute()
        for f in existing.get('files',[]): drive_service.files().delete(fileId=f['id']).execute()
        media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype='application/pdf', resumable=True)
        uploaded = drive_service.files().create(body={'name':file_name,'parents':[DRIVE_UPLOAD_FOLDER_ID]}, media_body=media, fields='id,webViewLink').execute()
        file_id = uploaded.get('id')
        drive_service.permissions().create(fileId=file_id, body={'type':'anyone','role':'reader'}).execute()
        link = uploaded.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view")
        return True, link, "✅ تم رفع الملف"
    except Exception as e: return False, "", f"❌ {str(e)}"

def save_memo_deposit(memo_number, file_link):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":[{"range":f"Feuille 1!V{row_idx}","values":[["مودعة"]]},{"range":f"Feuille 1!W{row_idx}","values":[[file_link]]},{"range":f"Feuille 1!X{row_idx}","values":[[timestamp]]}]}).execute()
        clear_cache_and_reload(); return True, "✅ تم حفظ الإيداع"
    except Exception as e: return False, f"❌ {str(e)}"

def save_approval_declaration(memo_number, prof_name, signature, declaration_text):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!AB{row_idx}", valueInputOption="USER_ENTERED", body={"values":[[declaration_text]]}).execute()
        return True, "✅ تم حفظ التصريح"
    except Exception as e: return False, f"❌ {str(e)}"

def approve_memo_for_defense(memo_number):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!V{row_idx}", valueInputOption="USER_ENTERED", body={"values":[["قابلة للمناقشة"]]}).execute()
        clear_cache_and_reload(); return True, "✅ تمت الموافقة"
    except Exception as e: return False, f"❌ {str(e)}"

def reject_memo_and_reopen(memo_number, prof_name, rejection_reason):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rejection_full = f"مرفوضة بتاريخ {timestamp} | المشرف: {prof_name} | السبب: {rejection_reason}"
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":[{"range":f"Feuille 1!V{row_idx}","values":[["مرفوضة"]]},{"range":f"Feuille 1!W{row_idx}","values":[[""]]},{"range":f"Feuille 1!X{row_idx}","values":[[""]]},{"range":f"Feuille 1!AB{row_idx}","values":[[rejection_full]]}]}).execute()
        clear_cache_and_reload(); return True, "✅ تم تسجيل الإعادة وفتح الإيداع"
    except Exception as e: return False, f"❌ {str(e)}"

def save_prof_notes(memo_number, prof_name, notes_text):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        note_full = f"ملاحظات المشرف {prof_name} [{timestamp}]: {notes_text}"
        sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!AB{row_idx}", valueInputOption="USER_ENTERED", body={"values":[[note_full]]}).execute()
        clear_cache_and_reload(); return True, "✅ تم حفظ الملاحظات"
    except Exception as e: return False, f"❌ {str(e)}"

def save_defense_schedule(memo_number, defense_date, defense_time, defense_room):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":[{"range":f"Feuille 1!Y{row_idx}","values":[[str(defense_date)]]},{"range":f"Feuille 1!Z{row_idx}","values":[[str(defense_time)]]},{"range":f"Feuille 1!AA{row_idx}","values":[[defense_room]]}]}).execute()
        clear_cache_and_reload(); return True, "✅ تم حفظ الموعد"
    except Exception as e: return False, f"❌ {str(e)}"

def save_jury(memo_number, president, exam1, exam2):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":[{"range":f"Feuille 1!AC{row_idx}","values":[[president]]},{"range":f"Feuille 1!AD{row_idx}","values":[[exam1]]},{"range":f"Feuille 1!AE{row_idx}","values":[[exam2]]}]}).execute()
        clear_cache_and_reload(); return True, "✅ تم حفظ اللجنة"
    except Exception as e: return False, f"❌ {str(e)}"

def save_notes_by_member(memo_number, member_role, notes_text):
    col_map = {"رئيس":"AG","مناقش1":"AH","مناقش2":"AI"}
    col = col_map.get(member_role)
    if not col: return False, "دور غير معروف"
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!{col}{row_idx}", valueInputOption="USER_ENTERED", body={"values":[[notes_text]]}).execute()
        clear_cache_and_reload(); return True, "✅ تم حفظ الملاحظات"
    except Exception as e: return False, f"❌ {str(e)}"

def publish_memos(memo_numbers=None):
    try:
        df_memos = load_memos()
        if memo_numbers:
            targets = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text).isin([normalize_text(m) for m in memo_numbers])]
        else:
            col = "حالة الإيداع"
            targets = df_memos[df_memos[col].astype(str).str.strip()=="قابلة للمناقشة"] if col in df_memos.columns else pd.DataFrame()
        if targets.empty: return False, "لا توجد مذكرات"
        updates = [{"range":f"Feuille 1!AF{idx+2}","values":[["نعم"]]} for idx in targets.index]
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates}).execute()
        clear_cache_and_reload(); return True, f"✅ تم نشر {len(updates)} مذكرة"
    except Exception as e: return False, f"❌ {str(e)}"

def update_progress(memo_number, progress_value):
    try:
        df_memos = load_memos()
        row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==normalize_text(memo_number)]
        if row.empty: return False, "❌ غير موجودة"
        row_idx = row.index[0]+2
        sheets_service.spreadsheets().values().update(spreadsheetId=MEMOS_SHEET_ID, range=f"Feuille 1!Q{row_idx}", valueInputOption="USER_ENTERED", body={"values":[[str(progress_value)]]}).execute()
        clear_cache_and_reload(); return True, "✅ تم تحديث نسبة التقدم"
    except Exception as e: return False, f"❌ {str(e)}"

def save_and_send_request(req_type, prof_name, memo_id, memo_title, details_text, status="قيد المراجعة"):
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_row = ["", timestamp, req_type, status, prof_name, memo_id, "", "", details_text, "", ""]
        sheets_service.spreadsheets().values().append(spreadsheetId=REQUESTS_SHEET_ID, range="Feuille 1!A2", valueInputOption="USER_ENTERED", body={"values":[new_row]}, insertDataOption="INSERT_ROWS").execute()
        return True, "✅ تم تسجيل الطلب"
    except Exception as e: return False, f"❌ {str(e)}"

def update_student_profile(username, phone, nin):
    try:
        df_students = load_students()
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        student_row = df_students[df_students["username_norm"]==normalize_text(username)]
        if student_row.empty: return False, "❌ لم يتم العثور على الطالب"
        row_idx = student_row.index[0]+2
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=STUDENTS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":[{"range":f"Feuille 1!M{row_idx}","values":[[phone]]},{"range":f"Feuille 1!U{row_idx}","values":[[nin]]}]}).execute()
        clear_cache_and_reload(); return True, "✅ تم التحديث"
    except Exception as e: return False, f"❌ {str(e)}"

def update_session_date_in_sheets(prof_name, date_str):
    try:
        df_memos = load_memos()
        masks = (df_memos["الأستاذ"].astype(str).str.strip()==prof_name) & (df_memos["تم التسجيل"].astype(str).str.strip()=="نعم")
        target_indices = df_memos[masks].index
        if target_indices.empty: return True, "لا توجد مذكرات"
        col_names = df_memos.columns.tolist()
        target_col = "موعد الجلسة القادمة"
        col_idx = col_names.index(target_col)+1 if target_col in col_names else len(col_names)
        col_l = col_letter(col_idx)
        updates = [{"range":f"Feuille 1!{col_l}{idx+2}","values":[[date_str]]} for idx in target_indices]
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates}).execute()
        return True, "تم التحديث"
    except Exception as e: return False, str(e)

def sync_student_registration_numbers():
    try:
        df_s = load_students(); df_m = load_memos(); updates = []
        df_s['رقم المذكرة_norm'] = df_s['رقم المذكرة'].astype(str).apply(normalize_text)
        students_with_memo = df_s[df_s['رقم المذكرة_norm'].notna() & (df_s['رقم المذكرة_norm']!="")]
        for index, row in df_m.iterrows():
            memo_num = normalize_text(row.get("رقم المذكرة",""))
            if not memo_num: continue
            matched = students_with_memo[students_with_memo["رقم المذكرة_norm"]==memo_num]
            if matched.empty: continue
            s1_name = str(row.get("الطالب الأول","")).strip(); s2_name = str(row.get("الطالب الثاني","")).strip()
            reg_s1=""; reg_s2=""
            for _, s_row in matched.iterrows():
                ln = s_row.get('لقب', s_row.get('اللقب','')); fn = s_row.get('إسم', s_row.get('الإسم',''))
                full = f"{ln} {fn}".strip()
                if full==s1_name: reg_s1 = normalize_text(s_row.get("رقم التسجيل",""))
                elif s2_name and full==s2_name: reg_s2 = normalize_text(s_row.get("رقم التسجيل",""))
            if not reg_s1 and len(matched)>0: reg_s1 = normalize_text(matched.iloc[0].get("رقم التسجيل",""))
            row_idx = index+2
            if reg_s1: updates.append({"range":f"Feuille 1!S{row_idx}","values":[[reg_s1]]})
            if reg_s2: updates.append({"range":f"Feuille 1!T{row_idx}","values":[[reg_s2]]})
        if updates:
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates}).execute()
            return True, f"✅ تم تحديث {len(updates)} خلية"
        return False, "ℹ️ لا توجد تغييرات"
    except Exception as e: return False, f"❌ {str(e)}"

def update_diploma_status(username, status_dict):
    try:
        df_students = load_students()
        df_students['username_norm'] = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
        row = df_students[df_students["username_norm"]==normalize_text(username)]
        if row.empty: return False, "❌ لم يتم العثور على الطالب"
        row_idx = row.index[0]+2
        updates = [{"range":f"Feuille 1!{k}{row_idx}","values":[[v]]} for k,v in status_dict.items()]
        if updates:
            sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=STUDENTS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates}).execute()
            clear_cache_and_reload(); return True, "✅ تم التحديث"
        return False, "لا شيء"
    except Exception as e: return False, f"❌ {str(e)}"

def get_students_of_professor(prof_name, df_memos):
    prof_memos = df_memos[(df_memos["الأستاذ"].astype(str).str.strip()==prof_name.strip()) & (df_memos["تم التسجيل"].astype(str).str.strip()=="نعم")]
    result = []
    for _, memo in prof_memos.iterrows():
        s1_name = str(memo.get("الطالب الأول","")).strip(); s1_reg = normalize_text(memo.get("رقم تسجيل الطالب 1",""))
        if s1_name and s1_name!="--" and s1_reg: result.append({"name":s1_name,"reg":s1_reg,"memo":memo.get("رقم المذكرة")})
        s2_name = str(memo.get("الطالب الثاني","")).strip(); s2_reg = normalize_text(memo.get("رقم تسجيل الطالب 2",""))
        if s2_name and s2_name!="--" and s2_reg: result.append({"name":s2_name,"reg":s2_reg,"memo":memo.get("رقم المذكرة")})
    return result

def format_datetime_ar(date_obj, time_str):
    days_ar = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
    return f"{days_ar[date_obj.weekday()]} {date_obj.strftime('%Y-%m-%d')} الساعة {time_str}"

def verify_student(username, password, df_students):
    valid, result = validate_username(username)
    if not valid: return False, result
    username = result; password = sanitize_input(password)
    if df_students.empty or "اسم المستخدم" not in df_students.columns: return False, "❌ خطأ في البيانات"
    db = df_students["اسم المستخدم"].astype(str).apply(normalize_text)
    student = df_students[db==username]
    if student.empty: return False, "❌ اسم المستخدم غير موجود"
    if str(student.iloc[0]["كلمة السر"]).strip() != password: return False, "❌ كلمة السر غير صحيحة"
    return True, student.iloc[0].to_dict()

def verify_professor(username, password, df_prof_memos):
    username = sanitize_input(username); password = sanitize_input(password)
    if df_prof_memos.empty or "إسم المستخدم" not in df_prof_memos.columns: return False, "❌ خطأ"
    db = df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text)
    mask = (db==username) & (df_prof_memos["كلمة المرور"].astype(str).str.strip()==password)
    prof = df_prof_memos[mask]
    if prof.empty: return False, "❌ بيانات غير صحيحة"
    return True, prof.iloc[0].to_dict()

def verify_admin(username, password):
    username = sanitize_input(username); password = sanitize_input(password)
    if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username]==password: return True, username
    return False, "❌ بيانات غير صحيحة"

def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    valid, result = validate_note_number(note_number)
    if not valid: return False, None, result
    note_number = result; prof_password = sanitize_input(prof_password)
    if df_memos.empty or df_prof_memos.empty: return False, None, "❌ خطأ في البيانات"
    row = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==note_number]
    if row.empty: return False, None, "❌ رقم المذكرة غير موجود"
    row = row.iloc[0]
    if str(row.get("تم التسجيل","")).strip()=="نعم": return False, None, "❌ هذه المذكرة مسجلة مسبقاً"
    prof_row = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip()==row["الأستاذ"].strip()) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip()==prof_password)]
    if prof_row.empty: return False, None, "❌ كلمة سر المشرف غير صحيحة"
    return True, prof_row.iloc[0].to_dict(), None


def update_registration(note_number, student1, student2=None, s2_new_phone=None, s2_new_nin=None):
    try:
        df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_students = load_students()
        memo_data = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==str(note_number).strip()]
        if memo_data.empty: return False, "❌ رقم المذكرة غير موجود"
        prof_name = memo_data["الأستاذ"].iloc[0].strip()
        used_pw = st.session_state.prof_password.strip()
        potential = df_prof_memos[(df_prof_memos["الأستاذ"].astype(str).str.strip()==prof_name) & (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip()==used_pw)]
        if potential.empty: return False, "❌ بيانات الأستاذ غير متطابقة"
        target = potential[potential["رقم المذكرة"].astype(str).apply(normalize_text)==str(note_number).strip()]
        if target.empty:
            target = potential[potential["تم التسجيل"].astype(str).str.strip()!="نعم"]
            if target.empty: return False, "❌ جميع المذكرات مسجلة"
        prof_row_idx = target.index[0]+2
        col_names = df_prof_memos.columns.tolist()
        s1_ln, s1_fn = get_student_name_display(student1)
        updates_prof = [
            {"range":f"Feuille 1!{col_letter(col_names.index('الطالب الأول')+1)}{prof_row_idx}","values":[[f"{s1_ln} {s1_fn}"]]},
            {"range":f"Feuille 1!{col_letter(col_names.index('تم التسجيل')+1)}{prof_row_idx}","values":[["نعم"]]},
            {"range":f"Feuille 1!{col_letter(col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}","values":[[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range":f"Feuille 1!{col_letter(col_names.index('رقم المذكرة')+1)}{prof_row_idx}","values":[[note_number]]}
        ]
        if student2:
            s2_ln, s2_fn = get_student_name_display(student2)
            updates_prof.append({"range":f"Feuille 1!{col_letter(col_names.index('الطالب الثاني')+1)}{prof_row_idx}","values":[[f"{s2_ln} {s2_fn}"]]})
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=PROF_MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates_prof}).execute()
        memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==str(note_number).strip()].index[0]+2
        memo_cols = df_memos.columns.tolist()
        reg1 = normalize_text(student1.get('رقم التسجيل',''))
        updates_memo = [
            {"range":f"Feuille 1!{col_letter(memo_cols.index('الطالب الأول')+1)}{memo_row_idx}","values":[[f"{s1_ln} {s1_fn}"]]},
            {"range":f"Feuille 1!{col_letter(memo_cols.index('تم التسجيل')+1)}{memo_row_idx}","values":[["نعم"]]},
            {"range":f"Feuille 1!{col_letter(memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}","values":[[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            {"range":f"Feuille 1!S{memo_row_idx}","values":[[reg1]]}
        ]
        if 'كلمة سر التسجيل' in memo_cols:
            updates_memo.append({"range":f"Feuille 1!{col_letter(memo_cols.index('كلمة سر التسجيل')+1)}{memo_row_idx}","values":[[used_pw]]})
        if student2:
            s2_ln2, s2_fn2 = get_student_name_display(student2); reg2 = normalize_text(student2.get('رقم التسجيل',''))
            updates_memo.append({"range":f"Feuille 1!{col_letter(memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}","values":[[f"{s2_ln2} {s2_fn2}"]]})
            updates_memo.append({"range":f"Feuille 1!T{memo_row_idx}","values":[[reg2]]})
        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=MEMOS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":updates_memo}).execute()
        students_cols = df_students.columns.tolist()
        s1_user = normalize_text(student1.get('اسم المستخدم',''))
        s1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text)==s1_user].index[0]+2
        sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s1_row_idx}", valueInputOption="USER_ENTERED", body={"values":[[note_number]]}).execute()
        if student2:
            s2_user = normalize_text(student2.get('اسم المستخدم',''))
            s2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text)==s2_user].index[0]+2
            sheets_service.spreadsheets().values().update(spreadsheetId=STUDENTS_SHEET_ID, range=f"Feuille 1!{col_letter(students_cols.index('رقم المذكرة')+1)}{s2_row_idx}", valueInputOption="USER_ENTERED", body={"values":[[note_number]]}).execute()
            s2_upd = []
            if s2_new_phone: s2_upd.append({"range":f"Feuille 1!M{s2_row_idx}","values":[[s2_new_phone]]})
            if s2_new_nin: s2_upd.append({"range":f"Feuille 1!U{s2_row_idx}","values":[[s2_new_nin]]})
            if s2_upd: sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=STUDENTS_SHEET_ID, body={"valueInputOption":"USER_ENTERED","data":s2_upd}).execute()
        time_module.sleep(2); clear_cache_and_reload(); time_module.sleep(1)
        df_students_updated = load_students()
        st.session_state.student1 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text)==s1_user].iloc[0].to_dict()
        if student2:
            s2_user2 = normalize_text(student2.get('اسم المستخدم',''))
            st.session_state.student2 = df_students_updated[df_students_updated["اسم المستخدم"].astype(str).apply(normalize_text)==s2_user2].iloc[0].to_dict()
        memo_d = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==str(note_number).strip()].iloc[0]
        send_email_to_professor(prof_name, memo_d, st.session_state.student1, st.session_state.get('student2'))
        return True, "✅ تم تسجيل المذكرة بنجاح!"
    except Exception as e:
        logger.error(f"Registration error: {e}"); return False, f"❌ {str(e)}"

def encode_str(s): return base64.urlsafe_b64encode(s.encode()).decode()
def decode_str(s):
    try: return base64.urlsafe_b64decode(s.encode()).decode()
    except: return ""

df_students = load_students(); df_memos = load_memos(); df_prof_memos = load_prof_memos(); df_requests = load_requests()
if df_students.empty or df_memos.empty or df_prof_memos.empty:
    st.error("❌ خطأ في تحميل البيانات."); st.stop()

def lookup_student(username):
    if df_students.empty: return None
    s = df_students[df_students["اسم المستخدم"].astype(str).apply(normalize_text)==normalize_text(username)]
    return s.iloc[0].to_dict() if not s.empty else None

def restore_session_from_url():
    if st.session_state.get('logged_in', False): return
    qp = st.query_params
    if 'ut' not in qp or 'un' not in qp: return
    user_type = qp['ut'] if isinstance(qp['ut'],str) else (qp['ut'][0] if qp['ut'] else "")
    username_enc = qp['un'] if isinstance(qp['un'],str) else (qp['un'][0] if qp['un'] else "")
    username = decode_str(username_enc)
    if not username: return
    if user_type=='student':
        s_data = lookup_student(username)
        if s_data:
            ph_ok,_ = is_phone_valid(str(s_data.get('الهاتف','')))
            nin_ok,_ = is_nin_valid(normalize_text(s_data.get('NIN','')))
            if ph_ok and nin_ok:
                st.session_state.user_type='student'; st.session_state.student1=s_data
                note_num = normalize_text(s_data.get('رقم المذكرة',''))
                st.session_state.mode = "view" if note_num else "register"
                st.session_state.logged_in = True
                if note_num:
                    mr = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==note_num]
                    if not mr.empty:
                        s2_name = str(mr.iloc[0].get("الطالب الثاني","")).strip()
                        if s2_name and s2_name!="--":
                            s2 = load_student2_for_memo(mr.iloc[0], normalize_text(s_data.get('رقم التسجيل','')), df_students)
                            if s2: st.session_state.student2=s2
    elif user_type=='professor':
        p = df_prof_memos[df_prof_memos["إسم المستخدم"].astype(str).apply(normalize_text)==normalize_text(username)]
        if not p.empty: st.session_state.professor=p.iloc[0].to_dict(); st.session_state.logged_in=True
    elif user_type=='admin':
        if username in ADMIN_CREDENTIALS: st.session_state.admin_user=username; st.session_state.logged_in=True
    if user_type: st.session_state.user_type=user_type

restore_session_from_url()

required_state = {
    'user_type':None,'logged_in':False,'student1':None,'student2':None,
    'professor':None,'admin_user':None,'memo_type':"فردية",
    'mode':"register",'note_number':"",'prof_password':"",
    'show_confirmation':False,'selected_memo_id':None,
    'admin_edit_student_user':None,'s2_phone_input':"",'s2_nin_input':"",
    'profile_incomplete':False,'profile_user_temp':None,'profile_error_msg':None,
    'admin_mode':None,'wizard_step':1,'generated_schedule':None,
    'prof_action':None
}
for k,v in required_state.items():
    if k not in st.session_state: st.session_state[k]=v

def logout():
    st.query_params.clear()
    for k in list(st.session_state.keys()): del st.session_state[k]
    for k,v in required_state.items(): st.session_state[k]=v
    st.rerun()


# ================================================================
# الصفحة الرئيسية
# ================================================================
if st.session_state.user_type is None:
    render_countdown_banner()
    st.markdown("<p style='text-align:center;color:#ffffff;font-size:1.05rem;'>جامعة محمد البشير الإبراهيمي — كلية الحقوق والعلوم السياسية</p>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;font-size:2rem;margin-bottom:2rem;'>📘 منصة مذكرات الماستر</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    for col, icon, title, desc, utype, btn_label in [
        (col1,"🎓","فضاء الطلبة","تسجيل المذكرة، إيداع النسخة النهائية، متابعة الملف","student","دخول الطلبة"),
        (col2,"📚","فضاء الأساتذة","متابعة المذكرات، مراجعة الإيداعات، تحديث التقدم","professor","دخول الأساتذة"),
        (col3,"⚙️","فضاء الإدارة","لوحة التحكم الكاملة، برنامج المناقشات","admin","دخول الإدارة"),
    ]:
        with col:
            st.markdown(f"""<div class="card" style="text-align:center;min-height:190px;display:flex;flex-direction:column;align-items:center;justify-content:center;"><div style="font-size:2.8rem;margin-bottom:10px;">{icon}</div><h3 style="margin:0 0 7px;">{title}</h3><p style="color:#ffffff!important;font-size:0.83rem;">{desc}</p></div>""", unsafe_allow_html=True)
            if st.button(btn_label, key=f"btn_{utype}", use_container_width=True):
                st.session_state.user_type=utype; st.rerun()

# ================================================================
# فضاء الطلبة
# ================================================================
elif st.session_state.user_type == "student":

    if st.session_state.get('profile_incomplete', False):
        render_countdown_banner()
        st.markdown("<h2>⚠️ استكمال الملف الشخصي</h2>", unsafe_allow_html=True)
        temp = st.session_state.profile_user_temp
        with st.form("complete_profile"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            dp = str(temp.get('الهاتف','')).strip()
            if dp in ['0','0.0','nan','-','']: dp=""
            dn = normalize_text(temp.get('NIN',''))
            if dn in ['0','nan','-','']: dn=""
            new_phone = st.text_input("📞 رقم الهاتف (10 أرقام)", value=dp)
            new_nin = st.text_input("🆔 رقم التعريف الوطني", value=dn)
            if st.form_submit_button("💾 حفظ والمتابعة", type="primary", use_container_width=True):
                ph_ok,_=is_phone_valid(new_phone); nin_ok,_=is_nin_valid(new_nin)
                if not ph_ok: st.error("❌ رقم الهاتف غير صالح")
                elif not nin_ok: st.error("❌ رقم التعريف غير صحيح")
                else:
                    username = normalize_text(temp.get('اسم المستخدم',''))
                    ok, msg = update_student_profile(username, new_phone, new_nin)
                    if ok:
                        st.session_state.profile_incomplete=False; st.session_state.logged_in=True
                        df_up = load_students()
                        st.session_state.student1 = df_up[df_up["اسم المستخدم"].astype(str).apply(normalize_text)==username].iloc[0].to_dict()
                        note_num = normalize_text(st.session_state.student1.get('رقم المذكرة',''))
                        st.session_state.mode = "view" if note_num else "register"
                        st.rerun()
                    else: st.error(msg)
            st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.logged_in:
        render_countdown_banner()
        c1,c2=st.columns([4,1])
        with c2:
            if st.button("رجوع"): st.session_state.user_type=None; st.rerun()
        st.markdown("<h2>🎓 فضاء الطلبة</h2>", unsafe_allow_html=True)
        with st.form("student_login"):
            st.write("### 🔐 تسجيل الدخول")
            username1 = st.text_input("اسم المستخدم")
            password1 = st.text_input("كلمة السر", type="password")
            if st.form_submit_button("دخول"):
                valid, result = verify_student(username1, password1, df_students)
                if not valid: st.error(result)
                else:
                    ph_ok,_=is_phone_valid(str(result.get('الهاتف','')))
                    nin_ok,_=is_nin_valid(normalize_text(result.get('NIN','')))
                    if ph_ok and nin_ok:
                        st.session_state.student1=result
                        note_num = normalize_text(result.get('رقم المذكرة',''))
                        if note_num:
                            st.session_state.mode="view"
                            mr = df_memos[df_memos["رقم المذكرة"].astype(str).apply(normalize_text)==note_num]
                            if not mr.empty:
                                s2_name = str(mr.iloc[0].get("الطالب الثاني","")).strip()
                                if s2_name and s2_name!="--":
                                    s2 = load_student2_for_memo(mr.iloc[0], normalize_text(result.get('رقم التسجيل','')), df_students)
                                    if s2: st.session_state.student2=s2
                        else: st.session_state.mode="register"
                        st.session_state.logged_in=True
                        st.query_params['ut']='student'
                        st.query_params['un']=encode_str(normalize_text(result.get('اسم المستخدم','')))
                        st.rerun()
                    else:
                        st.session_state.profile_user_temp=result
                        st.session_state.profile_incomplete=True
                        st.rerun()

    else:
        render_countdown_banner()
        s1 = st.session_state.student1; s2 = st.session_state.student2

        if st.session_state.mode == "register":
            c1,c2=st.columns([4,1])
            with c2:
                if st.button("خروج"): logout()
            st.markdown("<h2>📝 تسجيل مذكرة ماستر</h2>", unsafe_allow_html=True)
            registration_type = st.radio("نوع المذكرة:", ["فردية","ثنائية"], horizontal=True)
            username2=password2=None; student2_obj=None; s2_missing_info=False
            s2_new_phone_val=""; s2_new_nin_val=""
            if registration_type=="ثنائية":
                st.markdown("### 👥 بيانات الطالب الثاني")
                username2=st.text_input("اسم المستخدم الثاني")
                password2=st.text_input("كلمة السر الثاني", type="password")
                if username2 and password2:
                    v2,r2=verify_student(username2,password2,df_students)
                    if v2:
                        student2_obj=r2
                        ph_ok,_=is_phone_valid(str(r2.get('الهاتف','')))
                        nin_ok,_=is_nin_valid(normalize_text(r2.get('NIN','')))
                        if not ph_ok or not nin_ok:
                            s2_missing_info=True
                            st.warning("⚠️ بيانات الطالب الثاني ناقصة.")
                            s2_new_phone_val=st.text_input("📞 هاتف الطالب الثاني", key="s2_ph")
                            s2_new_nin_val=st.text_input("🆔 NIN الطالب الثاني", key="s2_nin")
                        else: st.success(f"✅ {r2.get('لقب','')} {r2.get('إسم','')} — بياناته مكتملة")
                    else: st.error(r2)
            st.markdown("### 🔍 المذكرات المتاحة")
            student_specialty = str(s1.get("التخصص","")).strip()
            available_memos_df = df_memos[(df_memos["تم التسجيل"].astype(str).str.strip()!="نعم") & (df_memos["التخصص"].astype(str).str.strip()==student_specialty)]
            def clean_text(val):
                v=str(val).strip(); return '' if v in ['','nan','None','NaN','-','0','0.0'] else v
            prof_counts = df_prof_memos.groupby("الأستاذ")["رقم المذكرة"].apply(lambda x: sum(1 for v in x if clean_text(v)!='')).to_dict()
            available_profs=[]
            if not available_memos_df.empty:
                for p in available_memos_df["الأستاذ"].unique():
                    if prof_counts.get(str(p).strip(),0)<4: available_profs.append(str(p).strip())
            available_profs=sorted(set(available_profs))
            if available_profs:
                sel_prof=st.selectbox("الأستاذ المشرف:", [""]+available_profs)
                if sel_prof:
                    pm=available_memos_df[available_memos_df["الأستاذ"].astype(str).str.strip()==sel_prof.strip()]
                    if not pm.empty:
                        st.success(f"✅ {len(pm)} عنوان متاح:")
                        for _,row in pm.iterrows():
                            st.markdown(f"""<div style="background:rgba(47,111,126,0.1);border:1px solid #2F6F7E;padding:10px;border-radius:8px;margin-bottom:5px;"><strong style="color:#FFD700;">{row['رقم المذكرة']}</strong> — <span style="color:#E2E8F0;">{row['عنوان المذكرة']}</span></div>""", unsafe_allow_html=True)
            else:
                st.warning("🔒 لا توجد أماكن شاغرة في تخصصك حالياً.")
            st.markdown("### ✍️ تسجيل المذكرة")
            c1,c2=st.columns([3,1])
            with c1: st.session_state.note_number=st.text_input("رقم المذكرة", value=st.session_state.note_number)
            with c2: st.session_state.prof_password=st.text_input("كلمة سر المشرف", type="password")
            if not st.session_state.show_confirmation:
                if st.button("المتابعة للتأكيد"):
                    if not st.session_state.note_number or not st.session_state.prof_password:
                        st.error("⚠️ يرجى إدخال بيانات المذكرة")
                    elif registration_type=="ثنائية" and not student2_obj:
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني")
                    elif s2_missing_info and (not s2_new_phone_val or not s2_new_nin_val):
                        st.error("❌ يرجى إدخال بيانات الطالب الثاني الناقصة")
                    else:
                        s1_perm=str(s1.get('التسجيل','')).strip()
                        if registration_type=="ثنائية":
                            s2_temp=student2_obj; s2_perm=str(s2_temp.get('التسجيل','')).strip()
                            if s1_perm!='1' and s2_perm!='1': st.error("⛔ لم يتم السماح لك بالتسجيل."); st.stop()
                        else:
                            fardiya=str(s1.get('فردية','')).strip()
                            if fardiya not in ["1","نعم"]: st.error("❌ لا يمكنك تسجيل مذكرة فردية"); st.stop()
                            if s1_perm!='1': st.error("⛔ لم يتم السماح لك."); st.stop()
                        st.session_state.show_confirmation=True
                        st.session_state.s2_phone_input=s2_new_phone_val if s2_missing_info else ""
                        st.session_state.s2_nin_input=s2_new_nin_val if s2_missing_info else ""
                        st.rerun()
            else:
                st.warning(f"⚠️ تأكيد التسجيل — المذكرة رقم: {st.session_state.note_number}")
                c1,c2=st.columns(2)
                with c1:
                    if st.button("تأكيد نهائي", type="primary"):
                        valid,_,err=verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                        if not valid: st.error(err); st.session_state.show_confirmation=False
                        else:
                            with st.spinner("⏳ جاري التسجيل..."):
                                s2_pass=student2_obj if registration_type=="ثنائية" else None
                                ok,msg=update_registration(st.session_state.note_number,s1,s2_pass,st.session_state.s2_phone_input,st.session_state.s2_nin_input)
                            if ok:
                                st.success(msg); st.balloons(); clear_cache_and_reload()
                                st.session_state.mode="view"; st.session_state.show_confirmation=False
                                time_module.sleep(2); st.rerun()
                            else: st.error(msg); st.session_state.show_confirmation=False
                with c2:
                    if st.button("إلغاء"): st.session_state.show_confirmation=False; st.rerun()

        elif st.session_state.mode == "view":
            c1,c2=st.columns([4,1])
            with c2:
                if st.button("خروج"): logout()
            note_num = normalize_text(s1.get('رقم المذكرة',''))
            df_memos_fresh = load_memos()
            memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).apply(normalize_text)==note_num].iloc[0]
            deposit_status = str(memo_info.get("حالة الإيداع","")).strip()
            deposit_link   = str(memo_info.get("رابط الملف","")).strip()
            deposit_date   = str(memo_info.get("تاريخ إيداع المذكرة","")).strip()
            def_date_m     = str(memo_info.get("تاريخ المناقشة","")).strip()
            def_time_m     = str(memo_info.get("توقيت المناقشة","")).strip()
            def_room_m     = str(memo_info.get("القاعة","")).strip()
            is_published   = str(memo_info.get("AF","")).strip()=="نعم" if "AF" in memo_info.index else False
            prof_name_m    = str(memo_info.get("الأستاذ","")).strip()

            # ── Hero الإيداع ──
            if deposit_status == "مرفوضة":
                rejection_raw = str(memo_info.get("توقيع المشرف","")).strip()
                reason_display = rejection_raw.split("السبب:")[-1].strip() if "السبب:" in rejection_raw else "يرجى مراجعة المشرف."
                st.markdown(f"""<div class="notif-card notif-card-rejected"><div class="notif-icon">🔴</div><div><div class="notif-title notif-title-rejected">المذكرة بحاجة لمراجعة</div><div class="notif-desc"><strong>ملاحظات المشرف:</strong><br>{reason_display}</div></div></div>""", unsafe_allow_html=True)

            if deposit_status in ["", "nan", "مرفوضة"] or not deposit_status:
                days_left = get_days_remaining()
                st.markdown(f"""<div class="deposit-hero"><span class="deposit-hero-icon">📤</span><div class="deposit-hero-title">يمكنك الآن إيداع مذكرتك النهائية</div><div class="deposit-hero-sub" style="color:#E2E8F0!important;">آخر أجل: <strong style="color:#FFD700;">14 ماي 2026</strong> — تبقى <strong style="color:{'#EF4444' if days_left<=7 else '#FFD700'};">{days_left} يوم</strong><br>ارفع نسخة PDF من مذكرتك. سيراجعها المشرف ويوافق أو يرسل ملاحظاته.</div></div>""", unsafe_allow_html=True)
                uploaded_pdf = st.file_uploader("📁 اختر ملف المذكرة (PDF فقط)", type=["pdf"], key="upload_pdf")
                if uploaded_pdf:
                    pdf_bytes = uploaded_pdf.read(); size_mb = len(pdf_bytes)/(1024*1024); uploaded_pdf.seek(0)
                    st.info(f"📊 حجم الملف: {size_mb:.1f} MB")
                    if size_mb > 50: st.error("❌ الحجم يتجاوز 10 MB")
                    else:
                        if st.button("📤 إيداع المذكرة الآن", type="primary", use_container_width=True):
                            with st.spinner("⏳ جاري رفع الملف..."):
                                ok, link, msg = upload_memo_to_drive(pdf_bytes, note_num, memo_info['عنوان المذكرة'])
                                if ok:
                                    s, m = save_memo_deposit(note_num, link)
                                    if s:
                                        s1_ln,s1_fn = get_student_name_display(st.session_state.student1)
                                        s1_display = f"{s1_ln} {s1_fn}".strip()
                                        s2_display = ""
                                        s2_obj_dep = load_student2_for_memo(memo_info, normalize_text(st.session_state.student1.get('رقم التسجيل','')), load_students())
                                        if s2_obj_dep:
                                            s2l,s2f = get_student_name_display(s2_obj_dep); s2_display=f"{s2l} {s2f}".strip()
                                        email_ok, email_msg = send_deposit_email_to_professor(prof_name_m, note_num, memo_info['عنوان المذكرة'], s1_display, s2_display)
                                        st.success("✅ تم إيداع مذكرتك! سيراجعها المشرف قريباً.")
                                        if email_ok: st.info("📧 تم إرسال إشعار للمشرف والإدارة.")
                                        else: st.warning(f"⚠️ فشل إرسال الإيميل للمشرف: {email_msg}")
                                        st.balloons(); clear_cache_and_reload(); time_module.sleep(2); st.rerun()
                                    else: st.error(m)
                                else: st.error(msg)
            elif deposit_status == "مودعة":
                st.markdown("""<div class="notif-card notif-card-waiting"><div class="notif-icon">🟡</div><div><div class="notif-title notif-title-waiting">مذكرتك مودعة — في انتظار مراجعة المشرف</div><div class="notif-desc">تم استلام ملفك. سيراجعه المشرف ويوافق أو يرسل ملاحظاته. ستتلقى إشعاراً فور اتخاذ القرار.</div></div></div>""", unsafe_allow_html=True)
                if deposit_date and deposit_date not in ["","nan"]: st.caption(f"📅 تاريخ الإيداع: {deposit_date}")
                if deposit_link and deposit_link not in ["","nan"]: st.markdown(f"📎 [عرض الملف المودع]({deposit_link})")
                st.markdown("""<div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:11px 15px;margin-top:9px;"><p style="color:#EF4444!important;margin:0;font-size:0.86rem;">⛔ الإيداع نهائي. للتصحيح تواصل مع الإدارة مباشرة.</p></div>""", unsafe_allow_html=True)
            elif deposit_status == "قابلة للمناقشة":
                st.markdown("""<div class="notif-card notif-card-approved"><div class="notif-icon">🟢</div><div><div class="notif-title notif-title-approved">مذكرتك معتمدة — قابلة للمناقشة ✓</div><div class="notif-desc">وافق المشرف على مذكرتك رسمياً. ستتلقى إشعاراً من الإدارة بموعد المناقشة قريباً.</div></div></div>""", unsafe_allow_html=True)
                if deposit_link and deposit_link not in ["","nan"]: st.markdown(f"📎 [عرض الملف المودع]({deposit_link})")

            # موعد المناقشة
            if is_published and def_date_m and def_date_m not in ["","nan"]:
                st.markdown(f"""<div class="defense-schedule-card"><h4 style="color:#818CF8!important;margin:0 0 6px;">📅 موعد مناقشتك</h4><div class="defense-info-grid"><div class="defense-info-item"><div class="defense-info-label">📆 التاريخ</div><div class="defense-info-value">{def_date_m}</div></div><div class="defense-info-item"><div class="defense-info-label">🕐 التوقيت</div><div class="defense-info-value">{def_time_m if def_time_m and def_time_m!='nan' else '—'}</div></div><div class="defense-info-item"><div class="defense-info-label">🏛️ القاعة</div><div class="defense-info-value">{def_room_m if def_room_m and def_room_m!='nan' else '—'}</div></div></div></div>""", unsafe_allow_html=True)
                president_s = str(memo_info.get("AC","")).strip() if "AC" in memo_info.index else ""
                exam1_s     = str(memo_info.get("AD","")).strip() if "AD" in memo_info.index else ""
                exam2_s     = str(memo_info.get("AE","")).strip() if "AE" in memo_info.index else ""
                if president_s and president_s not in ["","nan"]:
                    members_html = f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-president">🏛️</div><div class="jury-member-role role-president">رئيس اللجنة</div><div class="jury-member-name">{president_s}</div></div><div class="jury-member-card"><div class="jury-member-avatar avatar-supervisor">👨‍🏫</div><div class="jury-member-role role-supervisor">المشرف</div><div class="jury-member-name">{prof_name_m}</div></div>"""
                    if exam1_s and exam1_s!='nan': members_html += f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-examiner">📋</div><div class="jury-member-role role-examiner">مناقش 1</div><div class="jury-member-name">{exam1_s}</div></div>"""
                    if exam2_s and exam2_s not in ['','nan']: members_html += f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-examiner">📋</div><div class="jury-member-role role-examiner">مناقش 2</div><div class="jury-member-name">{exam2_s}</div></div>"""
                    st.markdown(f"""<div class="jury-card"><div class="jury-header"><div class="jury-header-icon">⚖️</div><div><div class="jury-header-title">لجنة مناقشة المذكرة رقم {note_num}</div><div class="jury-header-sub" style="color:rgba(255,255,255,0.85)!important;">{str(memo_info.get('عنوان المذكرة',''))[:60]}</div></div></div><div class="jury-members-grid">{members_html}</div></div>""", unsafe_allow_html=True)

            st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:22px 0;'>", unsafe_allow_html=True)

            tab_memo, tab_track, tab_notify = st.tabs(["📄 مذكرتي", "📂 ملف الشهادة", "🔔 الإشعارات"])

            with tab_memo:
                session_date = memo_info.get("موعد الجلسة القادمة","")
                session_html = f"<p>📅 <b>موعد الجلسة القادمة:</b> {session_date}</p>" if session_date and str(session_date) not in ["","nan"] else ""
                st.markdown(f"""<div class="card" style="border-top:3px solid #FFD700;"><h3>✅ مذكرتك المسجلة</h3><p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p><p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p><p><b>المشرف:</b> {prof_name_m}</p><p><b>التخصص:</b> {memo_info['التخصص']}</p>{session_html}</div>""", unsafe_allow_html=True)
                s1_ln,s1_fn=get_student_name_display(s1); s1_email=get_email_smart(s1)
                st.markdown(f"""<div class="card"><h4 style="color:#FFD700;">👤 الطالب الأول</h4><p><b>اللقب:</b> {s1_ln}</p><p><b>الإسم:</b> {s1_fn}</p><p><b>رقم التسجيل:</b> {s1.get('رقم التسجيل','')}</p><p><b>البريد:</b> {s1_email}</p></div>""", unsafe_allow_html=True)
                if s2:
                    s2_ln,s2_fn=get_student_name_display(s2); s2_email=get_email_smart(s2)
                    st.markdown(f"""<div class="card"><h4 style="color:#FFD700;">👤 الطالب الثاني</h4><p><b>اللقب:</b> {s2_ln}</p><p><b>الإسم:</b> {s2_fn}</p><p><b>رقم التسجيل:</b> {s2.get('رقم التسجيل','')}</p><p><b>البريد:</b> {s2_email}</p></div>""", unsafe_allow_html=True)

            with tab_track:
                st.subheader("📂 حالة ملف التخرج")
                def render_diploma(student_data, title):
                    cols_s = df_students.columns.tolist()
                    def gv(idx): return student_data.get(cols_s[idx],"غير محدد") if isinstance(student_data,dict) and len(cols_s)>idx else "غير محدد"
                    def badge(val):
                        v=str(val).strip()
                        if v in ["متوفر","مكتملة","كامل","جاهز","تم التسليم"]: return "status-available"
                        elif v in ["غير متوفر","ناقص","غير جاهز"]: return "status-unavailable"
                        return "status-pending"
                    items=[("📄 شهادة الميلاد",gv(14)),("📊 كشف M1",gv(15)),("📊 كشف M2",gv(16)),("📜 محضر المناقشة",gv(17)),("📂 حالة الملف",gv(18)),("🎓 حالة الشهادة",gv(19))]
                    rows_html="".join([f'<div class="diploma-item"><span>{label}</span><span class="status-badge {badge(val)}">{val}</span></div>' for label,val in items])
                    return f'<div class="card" style="border-right:4px solid #2F6F7E;"><h4 style="color:#FFD700;border-bottom:1px solid #334155;padding-bottom:9px;">{title}</h4>{rows_html}</div>'
                s1_ln,s1_fn=get_student_name_display(s1)
                st.markdown(render_diploma(s1, f"👤 {s1_ln} {s1_fn}"), unsafe_allow_html=True)

            with tab_notify:
                st.subheader("🔔 الإشعارات")
                df_reqs=load_requests()
                if note_num:
                    df_mn=load_memos()
                    my_row=df_mn[df_mn["رقم المذكرة"].astype(str).apply(normalize_text)==note_num]
                    sessions=pd.DataFrame()
                    if not my_row.empty:
                        my_prof=str(my_row.iloc[0]["الأستاذ"]).strip()
                        sessions=df_reqs[(df_reqs["النوع"]=="جلسة إشراف") & (df_reqs["الأستاذ"].astype(str).str.strip()==my_prof)]
                        if not sessions.empty:
                            last=sessions.iloc[-1]; details=""
                            try:
                                if len(last)>8:
                                    rv=str(last.iloc[8]).strip()
                                    if rv and rv.lower() not in ['nan','none']:
                                        dm=re.search(r'(\d{4}-\d{2}-\d{2})',rv)
                                        if dm:
                                            try: dt_obj=datetime.strptime(dm.group(0),'%Y-%m-%d'); details=rv.replace(dm.group(0), format_arabic_date(dt_obj))
                                            except: details=rv
                                        else: details=rv
                            except: pass
                            if details: st.markdown(f"""<div class="notif-card notif-card-scheduled"><div class="notif-icon">📅</div><div><div class="notif-title notif-title-scheduled">جلسة إشراف</div><div class="notif-desc">{details}</div></div></div>""", unsafe_allow_html=True)
                    my_reqs=df_reqs[df_reqs["رقم المذكرة"].astype(str).apply(normalize_text)==note_num]
                    if my_reqs.empty and sessions.empty: st.info("لا توجد إشعارات جديدة.")
                    else:
                        for _,r in my_reqs.iterrows():
                            rt=r['النوع']; details=""
                            if len(r)>8:
                                rv=str(r.iloc[8]).strip()
                                if rv and rv.lower() not in ['nan','none']: details=rv
                            st.markdown(f"""<div class="card" style="border-right:4px solid #F59E0B;"><h4>{rt}</h4><p>الحالة: <b>{r.get('الحالة','—')}</b></p>{'<p>'+details+'</p>' if details else ''}</div>""", unsafe_allow_html=True)


# ================================================================
# فضاء الأساتذة
# ================================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        render_countdown_banner()
        c1,c2=st.columns([4,1])
        with c2:
            if st.button("رجوع"): st.session_state.user_type=None; st.rerun()
        st.markdown("<h2>📚 فضاء الأساتذة</h2>", unsafe_allow_html=True)
        with st.form("prof_login"):
            c1,c2=st.columns(2)
            with c1: u=st.text_input("اسم المستخدم")
            with c2: p=st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v,r=verify_professor(u,p,df_prof_memos)
                if not v: st.error(r)
                else:
                    st.session_state.professor=r; st.session_state.logged_in=True
                    st.query_params['ut']='professor'
                    st.query_params['un']=encode_str(normalize_text(r.get('إسم المستخدم','')))
                    st.rerun()
    else:
        render_countdown_banner()
        prof=st.session_state.professor; prof_name=prof["الأستاذ"]

        if st.session_state.get('selected_memo_id'):
            memo_id=st.session_state.selected_memo_id
            df_m_fresh=load_memos()
            current_memo=df_m_fresh[df_m_fresh["رقم المذكرة"].astype(str).apply(normalize_text)==memo_id].iloc[0]
            student_info=get_student_info_from_memo(current_memo, df_students)
            c_back,_=st.columns([1,6])
            with c_back:
                if st.button("⬅️ العودة"): st.session_state.selected_memo_id=None; st.session_state.prof_action=None; st.rerun()

            deposit_status=str(current_memo.get("حالة الإيداع","")).strip()
            deposit_link=str(current_memo.get("رابط الملف","")).strip()
            deposit_date=str(current_memo.get("تاريخ إيداع المذكرة","")).strip()

            prog_val=str(current_memo.get('نسبة التقدم','0')).strip()
            try: prog_int=int(prog_val) if prog_val else 0
            except: prog_int=0

            dep_color={"مودعة":"#F59E0B","قابلة للمناقشة":"#10B981","مرفوضة":"#EF4444"}.get(deposit_status,"#ffffff")
            dep_label={"مودعة":"📤 مودعة","قابلة للمناقشة":"🟢 معتمدة","مرفوضة":"🔴 معادة"}.get(deposit_status,"⏳ لم تودَع")
            st.markdown(f"""<div style="background:linear-gradient(135deg,#0F2942,#1A3A5C);border-radius:16px;padding:20px 24px;margin-bottom:22px;border:1px solid rgba(47,111,126,0.3);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;"><div><p style="font-size:2.4rem;font-weight:900;color:#FFD700;margin:0;line-height:1;">{current_memo['رقم المذكرة']}</p><p style="font-size:1.05rem;font-weight:700;color:#ffffff;margin:4px 0;">{current_memo['عنوان المذكرة']}</p><p style="font-size:0.83rem;color:#ffffff;margin:0;">{current_memo['التخصص']} | نسبة الإنجاز: {prog_int}%</p></div><div style="background:rgba(0,0,0,0.25);color:#ffffff;padding:7px 16px;border-radius:20px;font-weight:700;font-size:0.88rem;border:1px solid {dep_color};">{dep_label}</div></div>""", unsafe_allow_html=True)

            cards_html = f"""<div class="student-card"><h4 style="color:#FFD700;margin-top:0;">الطالب الأول</h4><p style="font-size:1.1rem;font-weight:700;margin:9px 0 3px;">{student_info['s1_name']}</p><p style="color:#E2E8F0;font-size:0.83rem;">رقم التسجيل: {student_info['s1_reg'] or '—'}</p><div style="background:rgba(16,185,129,0.07);border-radius:8px;padding:7px;margin-top:10px;color:#10B981;font-size:0.83rem;">📧 {student_info['s1_email'] or 'غير متوفر'}</div></div>"""
            if student_info['s2_name']:
                cards_html += f"""<div class="student-card"><h4 style="color:#FFD700;margin-top:0;">الطالب الثاني</h4><p style="font-size:1.1rem;font-weight:700;margin:9px 0 3px;">{student_info['s2_name']}</p><p style="color:#E2E8F0;font-size:0.83rem;">رقم التسجيل: {student_info['s2_reg'] or '—'}</p><div style="background:rgba(16,185,129,0.07);border-radius:8px;padding:7px;margin-top:10px;color:#10B981;font-size:0.83rem;">📧 {student_info['s2_email'] or 'غير متوفر'}</div></div>"""
            st.markdown(f'<div class="students-grid">{cards_html}</div>', unsafe_allow_html=True)

            c1,c2=st.columns(2)
            with c1:
                new_prog=st.selectbox("📊 تحديث نسبة التقدم:",["0%","10% - ضبط المقدمة","30% - الفصل الأول","60% - الفصل الثاني","80% - الخاتمة","100% - مكتملة"],key=f"prog_{memo_id}")
                if st.button("حفظ التقدم",key=f"save_prog_{memo_id}"):
                    mapping={"0%":0,"10% - ضبط المقدمة":10,"30% - الفصل الأول":30,"60% - الفصل الثاني":60,"80% - الخاتمة":80,"100% - مكتملة":100}
                    ok,msg=update_progress(memo_id,mapping[new_prog])
                    if ok: st.success(msg); time_module.sleep(1); st.rerun()
                    else: st.error(msg)

            st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;margin-bottom:16px;'>📥 حالة إيداع المذكرة</h3>", unsafe_allow_html=True)

            if not deposit_status or deposit_status in ["nan",""]:
                st.markdown("""<div style="background:rgba(47,111,126,0.08);border:1px solid rgba(47,111,126,0.3);border-radius:14px;padding:22px;text-align:center;"><div style="font-size:2.3rem;">⏳</div><p style="color:#ffffff!important;font-size:0.95rem;margin:7px 0;">لم يودع الطالب المذكرة بعد.</p></div>""", unsafe_allow_html=True)

            elif deposit_status == "مودعة":
                st.markdown(f"""<div style="background:linear-gradient(135deg,rgba(245,158,11,0.1),rgba(245,158,11,0.04));border:2px solid rgba(245,158,11,0.42);border-radius:16px;padding:20px;margin-bottom:16px;"><h4 style="color:#F59E0B!important;margin:0 0 5px;">📥 مذكرة بانتظار مراجعتك</h4><p style="color:#E2E8F0!important;margin:0;font-size:0.88rem;">تاريخ الإيداع: <strong style="color:#FFD700;">{deposit_date if deposit_date and deposit_date!='nan' else '—'}</strong></p></div>""", unsafe_allow_html=True)
                if deposit_link and deposit_link not in ["","nan"]:
                    st.markdown(f"""<div style="text-align:center;margin:14px 0 20px;"><a href="{deposit_link}" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#1E3A5F,#2F6F7E);color:#ffffff;padding:15px 38px;border-radius:13px;text-decoration:none;font-size:1.05rem;font-weight:700;box-shadow:0 8px 22px rgba(47,111,126,0.38);">📄 الاطلاع على المذكرة المودعة</a></div>""", unsafe_allow_html=True)
                if not st.session_state.get('prof_action'):
                    st.markdown("#### اتخذ قرارك:")
                    ca,cb,cc=st.columns(3)
                    with ca:
                        if st.button("✅ موافقة على المذكرة",use_container_width=True,key=f"btn_approve_{memo_id}"):
                            st.session_state['prof_action']='approve'; st.rerun()
                    with cb:
                        if st.button("🔴 إعادة للمراجعة",use_container_width=True,key=f"btn_reject_{memo_id}"):
                            st.session_state['prof_action']='reject'; st.rerun()
                    with cc:
                        if st.button("💬 إرسال ملاحظات",use_container_width=True,key=f"btn_notes_{memo_id}"):
                            st.session_state['prof_action']='notes'; st.rerun()

                elif st.session_state.get('prof_action') == 'approve':
                    s1_name_ap=str(current_memo.get("الطالب الأول","")).strip()
                    s2_name_ap=str(current_memo.get("الطالب الثاني","")).strip()
                    students_str_ap=s1_name_ap
                    if s2_name_ap and s2_name_ap not in ["","nan","--"]: students_str_ap+=f" و {s2_name_ap}"
                    declaration_text_base = f"بعنوان «{current_memo.get('عنوان المذكرة','')}» للطالب(ين) {students_str_ap}، هي النسخة النهائية المودعة وهي التي ستُعرض على لجنة المناقشة ولن يُقبل أي تعديل بعد هذا التصريح."
                    st.markdown("""<div class="declaration-card"><div class="declaration-card-header"><div class="declaration-card-title">📋 التصريح الرسمي بالموافقة</div><div class="declaration-card-sub">يُرجى إكمال جميع الخطوات. هذا التصريح موثق ولا يمكن التراجع عنه.</div></div><div class="declaration-card-body">""", unsafe_allow_html=True)
                    st.markdown('<div class="declaration-step-label">① عدد صفحات المذكرة (دليل على اطلاعك الكامل)</div>', unsafe_allow_html=True)
                    page_count = st.number_input("عدد الصفحات",min_value=0,max_value=999,value=0,step=1,key=f"pages_{memo_id}")
                    st.markdown(f"""<div class="declaration-step-label" style="margin-top:14px;">② نص التصريح الذي سيُحفظ</div><div class="declaration-preview">أنا الأستاذ <strong>{prof_name}</strong>، أصرّح بأن المذكرة رقم <strong>{memo_id}</strong>، عدد الصفحات: <strong>{page_count}</strong>، {declaration_text_base}</div>""", unsafe_allow_html=True)
                    st.markdown('<div class="declaration-step-label" style="margin-top:14px;">③ الإقرار والتوقيع الإلكتروني</div>', unsafe_allow_html=True)
                    agree_check = st.checkbox("✅ أقرّ بصحة هذا التصريح وأتحمل مسؤوليته",key=f"agree_{memo_id}")
                    st.markdown(f"""<div style="background:rgba(47,111,126,0.07);border:1px dashed #2F6F7E;border-radius:8px;padding:8px 13px;margin:7px 0 5px;"><p style="color:#E2E8F0!important;font-size:0.78rem;margin:0;">الاسم المسجل: <strong style="color:#FFD700;">{prof_name}</strong></p></div>""", unsafe_allow_html=True)
                    signature = st.text_input("التوقيع — اكتب اسمك الكامل بالضبط",placeholder=f"اكتب: {prof_name}",key=f"sig_{memo_id}")
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    col_ok,col_cancel=st.columns(2)
                    with col_ok:
                        if not st.session_state.get(f"confirm_step_{memo_id}",False):
                            if st.button("📋 متابعة للتأكيد النهائي",type="primary",use_container_width=True,key=f"pre_approve_{memo_id}"):
                                errs=[]
                                if not agree_check: errs.append("❌ يجب الإقرار أولاً")
                                if page_count < 60: errs.append("❌ عدد الصفحات يجب أن يكون 60 على الأقل")
                                if not signature.strip(): errs.append("❌ التوقيع فارغ")
                                elif signature.strip()!=prof_name.strip(): errs.append(f"❌ التوقيع غير مطابق — اكتب: «{prof_name}»")
                                if errs:
                                    for e in errs: st.error(e)
                                else:
                                    st.session_state[f"confirm_step_{memo_id}"]=True
                                    st.session_state[f"sig_value_{memo_id}"]=signature.strip()
                                    st.session_state[f"pages_value_{memo_id}"]=page_count
                                    st.rerun()
                        else:
                            st.markdown("""<div style="background:rgba(239,68,68,0.09);border:2px solid #EF4444;border-radius:13px;padding:18px;text-align:center;margin-bottom:13px;"><div style="font-size:1.7rem;">⚠️</div><h4 style="color:#EF4444!important;margin:7px 0;">تأكيد نهائي — لا رجعة فيه</h4><p style="color:#E2E8F0!important;font-size:0.86rem;">ستُحفظ موافقتك وتُرسل الإشعارات للطلبة والإدارة.</p></div>""", unsafe_allow_html=True)
                            if st.button("✅ نعم، أوافق نهائياً",type="primary",use_container_width=True,key=f"final_approve_{memo_id}"):
                                sig_saved=st.session_state.get(f"sig_value_{memo_id}","")
                                pages_saved=st.session_state.get(f"pages_value_{memo_id}",page_count)
                                with st.spinner("⏳ جاري حفظ التصريح..."):
                                    timestamp_ap=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    full_declaration=f"تصريح: {prof_name} | توقيع: {sig_saved} | {timestamp_ap} | أنا الأستاذ {prof_name}، أصرّح بأن المذكرة رقم {memo_id} عدد الصفحات: {pages_saved} {declaration_text_base}"
                                    save_approval_declaration(memo_id, prof_name, sig_saved, full_declaration)
                                    ok,msg=approve_memo_for_defense(memo_id)
                                    if ok:
                                        df_sf=load_students(); df_sf['رقم التسجيل_norm']=df_sf['رقم التسجيل'].astype(str).apply(normalize_text)
                                        memo_vals=current_memo.tolist() if hasattr(current_memo,'tolist') else list(current_memo.values())
                                        r1=normalize_text(current_memo.get("رقم تسجيل الطالب 1",memo_vals[18] if len(memo_vals)>18 else ""))
                                        r2=normalize_text(current_memo.get("رقم تسجيل الطالب 2",memo_vals[19] if len(memo_vals)>19 else ""))
                                        s1d=s2d=None
                                        if r1 and r1 not in ["","nan"]:
                                            rr=df_sf[df_sf["رقم التسجيل_norm"]==r1]
                                            if not rr.empty: s1d=rr.iloc[0].to_dict()
                                        if r2 and r2 not in ["","nan"]:
                                            rr=df_sf[df_sf["رقم التسجيل_norm"]==r2]
                                            if not rr.empty: s2d=rr.iloc[0].to_dict()
                                        send_approval_email_to_students(memo_id,str(current_memo.get('عنوان المذكرة','')),prof_name,s1d,s2d)
                                        for k in [f"confirm_step_{memo_id}",f"sig_value_{memo_id}",f"pages_value_{memo_id}"]: st.session_state.pop(k,None)
                                        st.session_state['prof_action']=None
                                        st.success("✅ تمت الموافقة وحُفظ التصريح. تم إشعار الطلبة.")
                                        st.balloons(); clear_cache_and_reload(); time_module.sleep(2); st.rerun()
                                    else: st.error(msg)
                    with col_cancel:
                        if st.button("إلغاء",use_container_width=True,key=f"cancel_ap_{memo_id}"):
                            st.session_state['prof_action']=None; st.session_state.pop(f"confirm_step_{memo_id}",None); st.rerun()

                elif st.session_state.get('prof_action') == 'reject':
                    st.markdown("""<div style="background:rgba(239,68,68,0.07);border:2px solid rgba(239,68,68,0.32);border-radius:15px;padding:20px;margin-bottom:14px;"><h4 style="color:#EF4444!important;margin:0 0 9px;">🔴 إعادة المذكرة للمراجعة</h4><p style="color:#E2E8F0!important;font-size:0.86rem;margin:0;">سيتم إعادة فتح الإيداع للطالب وإرسال ملاحظاتك بالبريد الإلكتروني وعلى المنصة.</p></div>""", unsafe_allow_html=True)
                    rejection_reason=st.text_area("📋 سبب الإعادة وملاحظاتك التفصيلية:",height=140,placeholder="اكتب ملاحظاتك بدقة...",key=f"rej_reason_{memo_id}")
                    cr1,cr2=st.columns(2)
                    with cr1:
                        if st.button("🔴 تأكيد الإعادة للمراجعة",type="primary",use_container_width=True,key=f"confirm_rej_{memo_id}"):
                            if not rejection_reason.strip(): st.error("❌ يجب كتابة سبب الإعادة")
                            else:
                                with st.spinner("⏳ جاري الحفظ..."):
                                    ok,msg=reject_memo_and_reopen(memo_id,prof_name,rejection_reason)
                                    if ok:
                                        df_sf=load_students(); df_sf['رقم التسجيل_norm']=df_sf['رقم التسجيل'].astype(str).apply(normalize_text)
                                        memo_vals=current_memo.tolist() if hasattr(current_memo,'tolist') else list(current_memo.values())
                                        r1=normalize_text(current_memo.get("رقم تسجيل الطالب 1",memo_vals[18] if len(memo_vals)>18 else ""))
                                        r2=normalize_text(current_memo.get("رقم تسجيل الطالب 2",memo_vals[19] if len(memo_vals)>19 else ""))
                                        s1d=s2d=None
                                        if r1: rr=df_sf[df_sf["رقم التسجيل_norm"]==r1]; s1d=rr.iloc[0].to_dict() if not rr.empty else None
                                        if r2: rr=df_sf[df_sf["رقم التسجيل_norm"]==r2]; s2d=rr.iloc[0].to_dict() if not rr.empty else None
                                        send_rejection_email_to_students(memo_id,str(current_memo.get('عنوان المذكرة','')),prof_name,rejection_reason,s1d,s2d)
                                        st.session_state['prof_action']=None
                                        st.success("✅ تم تسجيل الإعادة. أُرسل إشعار للطلبة وفُتح الإيداع من جديد.")
                                        time_module.sleep(2); st.rerun()
                                    else: st.error(msg)
                    with cr2:
                        if st.button("إلغاء",use_container_width=True,key=f"cancel_rej_{memo_id}"):
                            st.session_state['prof_action']=None; st.rerun()

                elif st.session_state.get('prof_action') == 'notes':
                    st.markdown("""<div style="background:rgba(99,102,241,0.08);border:2px solid rgba(99,102,241,0.32);border-radius:15px;padding:20px;margin-bottom:14px;"><h4 style="color:#818CF8!important;margin:0 0 9px;">💬 إرسال ملاحظات للطالب</h4><p style="color:#E2E8F0!important;font-size:0.86rem;margin:0;">ستُرسل ملاحظاتك للطالب عبر الإيميل وتظهر على منصته. تبقى حالة الإيداع كما هي.</p></div>""", unsafe_allow_html=True)
                    notes_text=st.text_area("📝 ملاحظاتك:",height=130,placeholder="اكتب ملاحظاتك هنا...",key=f"notes_txt_{memo_id}")
                    cn1,cn2=st.columns(2)
                    with cn1:
                        if st.button("💬 إرسال الملاحظات",type="primary",use_container_width=True,key=f"send_notes_{memo_id}"):
                            if not notes_text.strip(): st.error("❌ يجب كتابة الملاحظات")
                            else:
                                ok,msg=save_prof_notes(memo_id,prof_name,notes_text)
                                if ok:
                                    df_sf=load_students(); df_sf['رقم التسجيل_norm']=df_sf['رقم التسجيل'].astype(str).apply(normalize_text)
                                    memo_vals=current_memo.tolist() if hasattr(current_memo,'tolist') else list(current_memo.values())
                                    r1=normalize_text(current_memo.get("رقم تسجيل الطالب 1",memo_vals[18] if len(memo_vals)>18 else ""))
                                    r2=normalize_text(current_memo.get("رقم تسجيل الطالب 2",memo_vals[19] if len(memo_vals)>19 else ""))
                                    s1d=s2d=None
                                    if r1: rr=df_sf[df_sf["رقم التسجيل_norm"]==r1]; s1d=rr.iloc[0].to_dict() if not rr.empty else None
                                    if r2: rr=df_sf[df_sf["رقم التسجيل_norm"]==r2]; s2d=rr.iloc[0].to_dict() if not rr.empty else None
                                    send_notes_email_to_students(memo_id,str(current_memo.get('عنوان المذكرة','')),prof_name,notes_text,s1d,s2d)
                                    st.session_state['prof_action']=None
                                    st.success("✅ تم إرسال الملاحظات للطالب."); time_module.sleep(1); st.rerun()
                                else: st.error(msg)
                    with cn2:
                        if st.button("إلغاء",use_container_width=True,key=f"cancel_notes_{memo_id}"):
                            st.session_state['prof_action']=None; st.rerun()

            elif deposit_status == "قابلة للمناقشة":
                st.markdown(f"""<div style="background:rgba(16,185,129,0.09);border:2px solid #10B981;border-radius:15px;padding:20px;text-align:center;"><div style="font-size:2.3rem;">🟢</div><h4 style="color:#10B981!important;margin:9px 0;">المذكرة معتمدة — قابلة للمناقشة</h4><p style="color:#E2E8F0!important;">تم التصريح رسمياً وأُرسلت الإشعارات للطلبة.</p>{f'<a href="{deposit_link}" target="_blank" style="color:#10B981;font-size:0.88rem;">📄 عرض المذكرة المودعة</a>' if deposit_link and deposit_link!='nan' else ''}</div>""", unsafe_allow_html=True)

            st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.07);margin:20px 0;'>", unsafe_allow_html=True)
        else:
            c1,c2=st.columns([4,1])
            with c2:
                if st.button("خروج"): logout()
            st.markdown(f"<h2>📚 فضاء الأستاذ <span style='color:#FFD700;'>{prof_name}</span></h2>", unsafe_allow_html=True)
            df_m_fresh=load_memos()
            prof_memos=df_m_fresh[df_m_fresh["الأستاذ"].astype(str).str.strip()==prof_name.strip()]
            total=len(prof_memos); registered=len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip()=="نعم"]); available=total-registered; is_exhausted=registered>=4
            col_dep="حالة الإيداع"
            deposited_memos_pr=prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip()=="نعم"]
            if col_dep in deposited_memos_pr.columns:
                pending_deposit=deposited_memos_pr[deposited_memos_pr[col_dep].astype(str).str.strip()=="مودعة"]
                if not pending_deposit.empty:
                    items_html=""
                    for _,dep_memo in pending_deposit.iterrows():
                        dep_date=str(dep_memo.get("تاريخ إيداع المذكرة","")).strip()
                        items_html+=f"""<div class="prof-deposit-item"><div><div class="prof-deposit-memo-num">{dep_memo['رقم المذكرة']}</div><div class="prof-deposit-memo-title">{str(dep_memo['عنوان المذكرة'])[:52]}{'...' if len(str(dep_memo['عنوان المذكرة']))>52 else ''}</div><div class="prof-deposit-memo-date">📅 {dep_date if dep_date and dep_date!='nan' else '—'}</div></div><div style="background:rgba(245,158,11,0.1);color:#F59E0B;padding:4px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;border:1px solid rgba(245,158,11,0.28);">⏳ بانتظار مراجعتك</div></div>"""
                    st.markdown(f"""<div class="prof-deposit-alert"><div class="prof-deposit-alert-header"><div class="prof-deposit-alert-icon">📥</div><div><div class="prof-deposit-alert-title">لديك {len(pending_deposit)} مذكرة مودعة تنتظر مراجعتك</div><div class="prof-deposit-alert-sub">يرجى مراجعة كل مذكرة والموافقة عليها أو إعادتها مع الملاحظات</div></div></div><div class="prof-deposit-list">{items_html}</div></div>""", unsafe_allow_html=True)
            st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
            st.markdown(f'<div class="kpi-card"><div class="kpi-value">{total}</div><div class="kpi-label">إجمالي المذكرات</div></div><div class="kpi-card" style="border-top:3px solid #10B981;"><div class="kpi-value" style="color:#10B981;">{registered}</div><div class="kpi-label">مسجلة</div></div><div class="kpi-card" style="border-top:3px solid #F59E0B;"><div class="kpi-value" style="color:#F59E0B;">{available}</div><div class="kpi-label">متاحة</div></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            if is_exhausted: st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
            tab1,tab2,tab5=st.tabs(["المذكرات المسجلة","📅 جلسة إشراف","🎓 لجان المناقشة"])
            with tab1:
                st.subheader("المذكرات المسجلة")
                reg_memos=prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip()=="نعم"]
                if not reg_memos.empty:
                    cols=st.columns(2)
                    for i,(_,memo) in enumerate(reg_memos.iterrows()):
                        with cols[i%2]:
                            dep_s=str(memo.get(col_dep,"")).strip() if col_dep in memo.index else ""
                            dep_color_m={"مودعة":"#F59E0B","قابلة للمناقشة":"#10B981","مرفوضة":"#EF4444"}.get(dep_s,"#ffffff")
                            dep_label_m={"مودعة":"📤 مودعة","قابلة للمناقشة":"🟢 معتمدة","مرفوضة":"🔴 معادة"}.get(dep_s,"⏳ لم تودَع")
                            prog_v=str(memo.get('نسبة التقدم','0')).strip()
                            try: prog_i=int(prog_v) if prog_v else 0
                            except: prog_i=0
                            s_info=get_student_info_from_memo(memo,df_students)
                            st.markdown(f"""<div class="card" style="border-right:5px solid {dep_color_m};"><div style="display:flex;justify-content:space-between;margin-bottom:8px;"><h4 style="margin:0;color:#FFD700!important;">{memo['رقم المذكرة']}</h4><span style="background:rgba(0,0,0,0.25);color:#ffffff;padding:3px 9px;border-radius:12px;font-size:0.78rem;font-weight:700;border:1px solid {dep_color_m};">{dep_label_m}</span></div><p style="font-size:0.9rem;color:#ffffff!important;font-weight:600;margin-bottom:5px;">{str(memo['عنوان المذكرة'])[:55]}</p><p style="font-size:0.82rem;color:#E2E8F0!important;">{memo['التخصص']} | {prog_i}%</p><p style="font-size:0.9rem;color:#ffffff!important;">{s_info['s1_name']}</p>{f"<p style='font-size:0.88rem;color:#ffffff!important;'>{s_info['s2_name']}</p>" if s_info['s2_name'] else ""}<div class="progress-container"><div class="progress-bar" style="width:{prog_i}%;"></div></div></div>""", unsafe_allow_html=True)
                            if st.button(f"👉 فتح {memo['رقم المذكرة']}",key=f"open_{memo['رقم المذكرة']}",use_container_width=True):
                                st.session_state.selected_memo_id=memo['رقم المذكرة']; st.session_state.prof_action=None; st.rerun()
                else: st.info("لا توجد مذكرات مسجلة.")
            with tab2:
                st.subheader("📅 جدولة جلسة إشراف")
                with st.form("session_form"):
                    c1,c2=st.columns(2)
                    with c1: sel_date=st.date_input("تاريخ الجلسة",min_value=datetime.now().date())
                    with c2:
                        slots=[f"{h:02d}:{m:02d}" for h in range(8,16) for m in [0,30] if not (h==15 and m==30)]
                        sel_time=st.selectbox("التوقيت",slots)
                    if st.form_submit_button("📤 نشر الجلسة"):
                        if sel_date.weekday() in [4,5]: st.error("❌ لا يمكن الجمعة أو السبت")
                        else:
                            session_str=format_datetime_ar(sel_date,sel_time); details=f"موعد الجلسة: {session_str}"
                            students=get_students_of_professor(prof_name,df_m_fresh)
                            if not students: st.warning("لا يوجد طلاب مسجلون")
                            else:
                                ok1,_=save_and_send_request("جلسة إشراف",prof_name,"جماعي","جلسة إشراف",details,status="منجز")
                                update_session_date_in_sheets(prof_name,details)
                                ok3,_=send_session_emails(students,details,prof_name)
                                if ok1: st.success(f"✅ تم نشر الجلسة وإشعار {len(students)} طالب")
                                else: st.error("خطأ في الحفظ")
            # تاب كلمات السر محذوف
            # تاب المذكرات المتاحة محذوف
            with tab5:
                st.subheader("🎓 لجان المناقشة")
                df_m_jury=load_memos(); jury_memos=pd.DataFrame()
                if not df_m_jury.empty:
                    masks=[]
                    for cj,rj in [("الأستاذ","مشرف"),("AC","رئيس"),("AD","مناقش1"),("AE","مناقش2")]:
                        if cj in df_m_jury.columns:
                            mm=df_m_jury[df_m_jury[cj].astype(str).str.strip()==prof_name.strip()]
                            if not mm.empty: mm=mm.copy(); mm['صفتي']=rj; masks.append(mm)
                    if masks:
                        jury_memos=pd.concat(masks).drop_duplicates(subset=["رقم المذكرة"])
                        if "AF" in jury_memos.columns:
                            jury_memos=jury_memos[jury_memos["AF"].astype(str).str.strip()=="نعم"]
                if jury_memos.empty:
                    st.info("⏳ لا توجد مذكرات منشورة تخصك كعضو لجنة.")
                else:
                    for _,jm in jury_memos.iterrows():
                        jmid=str(jm.get("رقم المذكرة","")).strip(); role=jm.get('صفتي','')
                        dep_link_j=str(jm.get("رابط الملف","")).strip()
                        def_date_j=str(jm.get("تاريخ المناقشة","")).strip(); def_time_j=str(jm.get("توقيت المناقشة","")).strip(); def_room_j=str(jm.get("القاعة","")).strip()
                        with st.expander(f"📄 {jmid} — صفتك: {role}",expanded=False):
                            president_j=str(jm.get("AC","")).strip() if "AC" in jm.index else ""
                            exam1_j=str(jm.get("AD","")).strip() if "AD" in jm.index else ""
                            exam2_j=str(jm.get("AE","")).strip() if "AE" in jm.index else ""
                            sup_j=str(jm.get("الأستاذ","")).strip()
                            mem_html=f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-supervisor">👨‍🏫</div><div class="jury-member-role role-supervisor">المشرف</div><div class="jury-member-name">{sup_j}</div></div>"""
                            if president_j and president_j!='nan': mem_html=f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-president">🏛️</div><div class="jury-member-role role-president">رئيس اللجنة</div><div class="jury-member-name">{president_j}</div></div>"""+mem_html
                            if exam1_j and exam1_j!='nan': mem_html+=f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-examiner">📋</div><div class="jury-member-role role-examiner">مناقش 1</div><div class="jury-member-name">{exam1_j}</div></div>"""
                            if exam2_j and exam2_j not in ['','nan']: mem_html+=f"""<div class="jury-member-card"><div class="jury-member-avatar avatar-examiner">📋</div><div class="jury-member-role role-examiner">مناقش 2</div><div class="jury-member-name">{exam2_j}</div></div>"""
                            defense_html=""
                            if def_date_j and def_date_j!='nan': defense_html=f"""<div class="defense-info-grid"><div class="defense-info-item"><div class="defense-info-label">📆 التاريخ</div><div class="defense-info-value">{def_date_j}</div></div><div class="defense-info-item"><div class="defense-info-label">🕐 التوقيت</div><div class="defense-info-value">{def_time_j}</div></div><div class="defense-info-item"><div class="defense-info-label">🏛️ القاعة</div><div class="defense-info-value">{def_room_j}</div></div></div>"""
                            st.markdown(f"""<div class="jury-card"><div class="jury-header"><div class="jury-header-icon">⚖️</div><div><div class="jury-header-title">لجنة مناقشة رقم {jmid}</div><div class="jury-header-sub" style="color:rgba(255,255,255,0.85)!important;">{str(jm.get('عنوان المذكرة',''))[:58]}</div></div></div><div class="jury-members-grid">{mem_html}</div>{defense_html}</div>""", unsafe_allow_html=True)
                            if dep_link_j and dep_link_j!="nan":
                                st.markdown(f"""<div style="text-align:center;margin:10px 0;"><a href="{dep_link_j}" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#1E3A5F,#2F6F7E);color:#ffffff;padding:12px 28px;border-radius:11px;text-decoration:none;font-size:0.95rem;font-weight:700;box-shadow:0 6px 14px rgba(47,111,126,0.35);">📄 الاطلاع على المذكرة المودعة</a></div>""", unsafe_allow_html=True)
                            notes_col={"رئيس":"AG","مشرف":"AG","مناقش1":"AH","مناقش2":"AI"}.get(role,"AG")
                            curr_notes=str(jm.get(notes_col,"")).strip() if notes_col in jm.index else ""
                            if curr_notes in ["nan",""]: curr_notes=""
                            st.markdown("**📝 ملاحظاتك الأولية:**")
                            new_notes=st.text_area("",value=curr_notes,height=90,key=f"jury_notes_{jmid}_{role}")
                            if st.button("💾 حفظ",key=f"save_jury_notes_{jmid}_{role}",use_container_width=True):
                                ok,msg=save_notes_by_member(jmid,role,new_notes)
                                if ok: st.success(msg); clear_cache_and_reload()
                                else: st.error(msg)


# ================================================================
# فضاء الإدارة
# ================================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        render_countdown_banner()
        c1,c2=st.columns([4,1])
        with c2:
            if st.button("رجوع"): st.session_state.user_type=None; st.rerun()
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        with st.form("admin_login"):
            u=st.text_input("اسم المستخدم"); p=st.text_input("كلمة المرور",type="password")
            if st.form_submit_button("دخول"):
                v,r=verify_admin(u,p)
                if not v: st.error(r)
                else:
                    st.session_state.admin_user=r; st.session_state.logged_in=True
                    st.query_params['ut']='admin'; st.query_params['un']=encode_str(st.session_state.admin_user); st.rerun()
    else:
        render_countdown_banner()
        c1,c2=st.columns([4,1])
        with c2:
            if st.button("خروج"): logout()
        st.header("📊 لوحة تحكم الإدارة")
        if st.button("🎓 برنامج المناقشات",key="open_wizard"):
            st.session_state['admin_mode']='defense_wizard'; st.session_state['wizard_step']=1; st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st_s=len(df_students); t_m=len(df_memos); r_m=len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip()=="نعم"])
        a_m=t_m-r_m; t_p=len(df_prof_memos["الأستاذ"].unique())
        memo_col=df_students["رقم المذكرة"].astype(str).str.strip()
        reg_st=(memo_col!="").sum(); unreg_st=(memo_col=="").sum()
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{st_s}</div><div class="kpi-label">الطلاب</div></div><div class="kpi-card"><div class="kpi-value">{t_p}</div><div class="kpi-label">الأساتذة</div></div><div class="kpi-card"><div class="kpi-value">{t_m}</div><div class="kpi-label">المذكرات</div></div><div class="kpi-card" style="border-top:3px solid #10B981;"><div class="kpi-value" style="color:#10B981;">{r_m}</div><div class="kpi-label">مسجلة</div></div><div class="kpi-card" style="border-top:3px solid #F59E0B;"><div class="kpi-value" style="color:#F59E0B;">{a_m}</div><div class="kpi-label">متاحة</div></div><div class="kpi-card" style="border-top:3px solid #10B981;"><div class="kpi-value" style="color:#10B981;">{reg_st}</div><div class="kpi-label">طلاب مسجلون</div></div><div class="kpi-card" style="border-top:3px solid #EF4444;"><div class="kpi-value" style="color:#EF4444;">{unreg_st}</div><div class="kpi-label">غير مسجلين</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8=st.tabs(["المذكرات","الطلاب","الأساتذة","تقارير","تحديث","الطلبات","📧 إيميلات","📅 جدولة"])
        with tab1:
            st.subheader("جدول المذكرات")
            f_status=st.selectbox("تصفية:",["الكل","مسجلة","متاحة"])
            if f_status=="مسجلة": dm=df_memos[df_memos["تم التسجيل"].astype(str).str.strip()=="نعم"]
            elif f_status=="متاحة": dm=df_memos[df_memos["تم التسجيل"].astype(str).str.strip()!="نعم"]
            else: dm=df_memos
            st.dataframe(dm,use_container_width=True,height=400)
        with tab2:
            st.subheader("الطلاب")
            q=st.text_input("بحث:")
            if st.session_state.get('admin_edit_student_user'):
                tu=st.session_state.admin_edit_student_user
                sd=df_students[df_students["اسم المستخدم"]==tu]
                if not sd.empty:
                    s=sd.iloc[0]; vals=s.tolist()
                    def gv(i): return vals[i] if len(vals)>i else ""
                    st.markdown(f"<h3>📝 ملف التخرج: {s.get('لقب','')} {s.get('إسم','')}</h3>", unsafe_allow_html=True)
                    with st.form("edit_diploma"):
                        c1,c2=st.columns(2)
                        with c1:
                            no=st.selectbox("شهادة الميلاد",["متوفر","غير متوفر"],index=0 if gv(14)=="متوفر" else 1)
                            np_v=st.selectbox("كشف M1",["متوفر","مدين","محول","خطأ"],index=["متوفر","مدين","محول","خطأ"].index(gv(15)) if gv(15) in ["متوفر","مدين","محول","خطأ"] else 0)
                            nq=st.selectbox("كشف M2",["غير متوفر","متوفر"],index=0 if gv(16)=="غير متوفر" else 1)
                        with c2:
                            nr=st.selectbox("محضر المناقشة",["غير متوفر","متوفر"],index=0 if gv(17)=="غير متوفر" else 1)
                            ns=st.selectbox("حالة الملف",["ناقص","كامل","كامل لحد الآن"],index=["ناقص","كامل","كامل لحد الآن"].index(gv(18)) if gv(18) in ["ناقص","كامل","كامل لحد الآن"] else 0)
                            nt_v=st.selectbox("حالة الشهادة",["غير جاهز","جاهز","تم التسليم"],index=["غير جاهز","جاهز","تم التسليم"].index(gv(19)) if gv(19) in ["غير جاهز","جاهز","تم التسليم"] else 0)
                        cs,cc=st.columns([1,4])
                        with cs:
                            if st.form_submit_button("💾 حفظ"):
                                ok,msg=update_diploma_status(tu,{'O':no,'P':np_v,'Q':nq,'R':nr,'S':ns,'T':nt_v})
                                if ok: st.success(msg); st.session_state.admin_edit_student_user=None; st.rerun()
                                else: st.error(msg)
                        with cc:
                            if st.form_submit_button("❌ إلغاء"): st.session_state.admin_edit_student_user=None; st.rerun()
            if q:
                name_cols=[c for c in df_students.columns if any(x in c.lower() for x in ['اسم','لقب','إسم'])]
                fst=df_students[df_students[name_cols].astype(str).apply(lambda x:x.str.contains(q,case=False,na=False)).any(axis=1)] if name_cols else df_students
                for idx,row in fst.iterrows():
                    st.markdown(f'<div style="background:rgba(255,255,255,0.03);padding:9px;border-radius:8px;border:1px solid #333;margin-bottom:4px;"><b>{row.get("لقب","")} {row.get("إسم","")}</b><br><small style="color:#E2E8F0;">{row.get("اسم المستخدم","")} | {row.get("رقم التسجيل","")}</small></div>', unsafe_allow_html=True)
                    c_e,_=st.columns([1,4])
                    with c_e:
                        if st.button("📝 ملف التخرج",key=f"edit_{idx}"):
                            st.session_state.admin_edit_student_user=row.get("اسم المستخدم"); st.rerun()
            else: st.dataframe(df_students,use_container_width=True,height=400)
        with tab3:
            st.subheader("توزيع الأساتذة")
            if "الأستاذ" in df_memos.columns:
                profs_list=sorted(df_memos["الأستاذ"].dropna().unique().tolist())
                sel_p=st.selectbox("اختر أستاذ:",["الكل"]+profs_list)
                if sel_p!="الكل": st.dataframe(df_memos[df_memos["الأستاذ"].astype(str).str.strip()==sel_p.strip()],use_container_width=True,height=400)
                else:
                    s_df=df_memos.groupby("الأستاذ").agg(total=("رقم المذكرة","count"),registered=("تم التسجيل",lambda x:(x.astype(str).str.strip()=="نعم").sum())).reset_index()
                    s_df["المتاحة"]=s_df["total"]-s_df["registered"]; s_df=s_df.rename(columns={"total":"الإجمالي","registered":"المسجلة"})
                    st.dataframe(s_df,use_container_width=True)
        with tab4:
            st.subheader("التحليل الإحصائي")
            c1,c2=st.columns(2)
            with c1: st.markdown("##### توزيع حسب التخصص"); st.bar_chart(df_memos.groupby("التخصص").size(),color="#2F6F7E")
            with c2: st.markdown("##### مسجلة حسب التخصص"); st.bar_chart(df_memos.groupby("التخصص")["تم التسجيل"].apply(lambda x:(x.astype(str).str.strip()=="نعم").sum()),color="#FFD700")
        with tab5:
            st.subheader("تحديث البيانات")
            if st.button("🔄 ربط أرقام التسجيل",type="primary"):
                with st.spinner("جاري المعالجة..."):
                    ok,msg=sync_student_registration_numbers()
                    if ok: st.success(msg); clear_cache_and_reload(); st.rerun()
                    else: st.info(msg)
            st.markdown("---")
            if st.button("تحديث من Google Sheets"):
                clear_cache_and_reload(); st.success("✅ تم التحديث"); st.rerun()
        with tab6:
            st.subheader("سجل الطلبات")
            st.dataframe(df_requests,use_container_width=True,height=500)
        with tab7:
            st.subheader("📧 إرسال إيميلات للأساتذة")
            mode_e=st.radio("نوع الإرسال:",["📩 أستاذ محدد","🚀 جميع الأساتذة"],horizontal=True)
            if mode_e=="📩 أستاذ محدد":
                pl=sorted(set([p for p in df_prof_memos["الأستاذ"].astype(str).dropna().tolist() if p.strip() and p.strip().lower()!="nan"]))
                sel_p2=st.selectbox("اختر الأستاذ:",pl,index=None)
                if st.button("إرسال الآن",type="secondary"):
                    if sel_p2:
                        ok,msg=send_welcome_email_to_one(sel_p2)
                        if ok: st.success(msg); st.balloons()
                        else: st.error(msg)
                    else: st.warning("اختر أستاذاً أولاً")
            else:
                st.info(f"سيتم الإرسال لـ {len(df_prof_memos)} أستاذ")
                if st.button("🚀 بدء الإرسال للجميع",type="primary"):
                    sent,failed,logs=send_welcome_emails_to_all_profs()
                    st.success(f"تم الإرسال لـ {sent} أستاذ.")
                    if failed>0: st.error(f"فشل لـ {failed} أستاذ.")
                    with st.expander("سجل العمليات"):
                        for log in logs: st.text(log)
        with tab8:
            st.subheader("📅 جدولة مواعيد المناقشات")
            df_memos_fresh8=load_memos(); col_deposit="حالة الإيداع"
            if col_deposit not in df_memos_fresh8.columns:
                st.info("لم يُودَع أي ملف بعد.")
            else:
                total_deposited=len(df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip().isin(["مودعة","قابلة للمناقشة"])])
                total_approved=len(df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip()=="قابلة للمناقشة"])
                c1,c2,c3=st.columns(3)
                with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#F59E0B;">{total_deposited}</div><div class="kpi-label">📤 مودعة</div></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#10B981;">{total_approved}</div><div class="kpi-label">🟢 قابلة للمناقشة</div></div>', unsafe_allow_html=True)
                defense_ready=df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip()=="قابلة للمناقشة"]
                if defense_ready.empty:
                    with c3: st.markdown('<div class="kpi-card"><div class="kpi-value">0</div><div class="kpi-label">📅 مجدولة</div></div>', unsafe_allow_html=True)
                    st.info("⏳ لا توجد مذكرات معتمدة للمناقشة.")
                else:
                    already_sched=len(defense_ready[defense_ready.get("تاريخ المناقشة",pd.Series(dtype=str)).astype(str).str.strip().isin(["","nan"])==False]) if "تاريخ المناقشة" in defense_ready.columns else 0
                    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-value" style="color:#FFD700;">{already_sched}</div><div class="kpi-label">📅 مجدولة</div></div>', unsafe_allow_html=True)
                    st.markdown("### 🟢 تحديد موعد المناقشة")
                    memo_options=defense_ready["رقم المذكرة"].astype(str).tolist()
                    selected_memo_def=st.selectbox("اختر المذكرة:",memo_options,key="admin_defense_select")
                    if selected_memo_def:
                        sel_row=defense_ready[defense_ready["رقم المذكرة"].astype(str)==selected_memo_def].iloc[0]
                        st.markdown(f"""<div class="card" style="border-top:3px solid #10B981;"><p>📄 <b>العنوان:</b> {sel_row.get('عنوان المذكرة','')}</p><p>👨‍🏫 <b>المشرف:</b> {sel_row.get('الأستاذ','')}</p><p>🎓 <b>التخصص:</b> {sel_row.get('التخصص','')}</p><p>👤 <b>الطالب الأول:</b> {sel_row.get('الطالب الأول','')}</p></div>""", unsafe_allow_html=True)
                        dep_link_adm=str(sel_row.get("رابط الملف","")).strip()
                        if dep_link_adm and dep_link_adm!="nan": st.markdown(f"📎 [عرض المذكرة المودعة]({dep_link_adm})")
                        curr_date=str(sel_row.get("تاريخ المناقشة","")).strip(); curr_time=str(sel_row.get("توقيت المناقشة","")).strip(); curr_room=str(sel_row.get("القاعة","")).strip()
                        ca,cb,cc=st.columns(3)
                        with ca:
                            try: default_date=datetime.strptime(curr_date,"%Y-%m-%d").date() if curr_date not in ["","nan"] else date.today()
                            except: default_date=date.today()
                            defense_date=st.date_input("📆 التاريخ",value=default_date,key=f"def_date_{selected_memo_def}")
                        with cb:
                            try: default_time_val=datetime.strptime(curr_time,"%H:%M").time() if curr_time not in ["","nan"] else datetime.strptime("09:00","%H:%M").time()
                            except: default_time_val=datetime.strptime("09:00","%H:%M").time()
                            defense_time=st.time_input("🕐 التوقيت",value=default_time_val,key=f"def_time_{selected_memo_def}")
                        with cc: defense_room=st.text_input("🏛️ القاعة",value=curr_room if curr_room not in ["","nan"] else "",key=f"def_room_{selected_memo_def}",placeholder="مثال: A01")
                        if st.button("💾 حفظ موعد المناقشة",type="primary",use_container_width=True,key=f"save_defense_{selected_memo_def}"):
                            if not defense_room.strip(): st.error("⚠️ يرجى إدخال اسم القاعة.")
                            else:
                                ok,msg=save_defense_schedule(selected_memo_def,str(defense_date),str(defense_time),defense_room.strip())
                                if ok:
                                    df_sf=load_students(); df_sf['رقم التسجيل_norm']=df_sf['رقم التسجيل'].astype(str).apply(normalize_text)
                                    sel_vals=sel_row.tolist() if hasattr(sel_row,'tolist') else list(sel_row.values())
                                    r1d=normalize_text(sel_row.get("رقم تسجيل الطالب 1",sel_vals[18] if len(sel_vals)>18 else ""))
                                    r2d=normalize_text(sel_row.get("رقم تسجيل الطالب 2",sel_vals[19] if len(sel_vals)>19 else ""))
                                    s1d=s2d=None
                                    if r1d and r1d not in ["","nan"]:
                                        rr=df_sf[df_sf["رقم التسجيل_norm"]==r1d]
                                        if not rr.empty: s1d=rr.iloc[0].to_dict()
                                    if r2d and r2d not in ["","nan"]:
                                        rr=df_sf[df_sf["رقم التسجيل_norm"]==r2d]
                                        if not rr.empty: s2d=rr.iloc[0].to_dict()
                                    email_ok,email_msg=send_defense_schedule_email(selected_memo_def,str(sel_row.get('عنوان المذكرة','')),str(sel_row.get('الأستاذ','')),str(defense_date),str(defense_time),defense_room.strip(),s1d,s2d)
                                    if email_ok: st.info("📧 تم إرسال إشعار الموعد للطلبة.")
                                    else: st.warning(f"تم الحفظ لكن فشل الإيميل: {email_msg}")
                                    st.success(msg); clear_cache_and_reload(); time_module.sleep(1); st.rerun()
                                else: st.error(msg)
                st.markdown("---")
                st.markdown("### 📋 جدول كامل بحالات الإيداع")
                display_cols=[c for c in ["رقم المذكرة","عنوان المذكرة","الأستاذ","التخصص","حالة الإيداع","تاريخ إيداع المذكرة","تاريخ المناقشة","توقيت المناقشة","القاعة"] if c in df_memos_fresh8.columns]
                filter_dep=st.selectbox("تصفية:",["الكل","مودعة","قابلة للمناقشة","لم تودَع"],key="filter_deposit_admin")
                if filter_dep=="مودعة": show_df=df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip()=="مودعة"]
                elif filter_dep=="قابلة للمناقشة": show_df=df_memos_fresh8[df_memos_fresh8[col_deposit].astype(str).str.strip()=="قابلة للمناقشة"]
                elif filter_dep=="لم تودَع": show_df=df_memos_fresh8[~df_memos_fresh8[col_deposit].astype(str).str.strip().isin(["مودعة","قابلة للمناقشة"])]
                else: show_df=df_memos_fresh8
                st.dataframe(show_df[display_cols],use_container_width=True,height=400)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#ffffff;font-size:11px;padding:16px;">إشراف مسؤول الميدان البروفيسور لخضر رفاف ©</div>', unsafe_allow_html=True)
