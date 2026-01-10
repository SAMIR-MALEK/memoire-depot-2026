import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText

# ---------------------------
# إعداد صفحة Streamlit
# ---------------------------
st.set_page_config(
    page_title="تسجيل مذكرة الماستر",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; max-width: 700px; margin: auto; }
label, h1, h2, h3, h4, p, span { color: #ffffff !important; }
button { background-color: #256D85 !important; color: white !important; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# إعداد اتصال Google Sheets
# ---------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(st.secrets["service_account"], scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

# ---------------------------
# معرفات الشيتات
# ---------------------------
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"          # شيت الطلبة
MEMOS_STATUS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"   # شيت حالة تسجيل المذكرات
MEMOS_SUPERVISOR_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE" # شيت المذكرات - الأساتذة

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_STATUS_RANGE = "Feuille 1!A1:N1000"
MEMOS_SUPERVISOR_RANGE = "Feuille 1!A1:L1000"

# ---------------------------
# دوال مساعدة
# ---------------------------
def col_letter(n):
    """تحويل رقم العمود إلى حرف"""
    result = ""
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result

# ---------------------------
# تحميل البيانات مع التخزين المؤقت
# ---------------------------
@st.cache_data(ttl=300)
def load_students():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE
    ).execute().get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos_status():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_STATUS_SHEET_ID, range=MEMOS_STATUS_RANGE
    ).execute().get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos_supervisor():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_SUPERVISOR_SHEET_ID, range=MEMOS_SUPERVISOR_RANGE
    ).execute().get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# ---------------------------
# التحقق من بيانات الطالب
# ---------------------------
def verify_student(username, password, df_students):
    """التحقق من اسم المستخدم وكلمة السر"""
    row = df_students[df_students["اسم المستخدم"].str.strip() == username.strip()]
    if row.empty:
        return False, "❌ اسم المستخدم غير موجود."
    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ كلمة السر غير صحيحة."
    if str(row.iloc[0]["رقم المذكرة"]).strip() != "":
        return False, "❌ الطالب سجل مذكرة من قبل!"
    return True, row.iloc[0]

# ---------------------------
# التحقق من المذكرة قبل التسجيل
# ---------------------------
def verify_memo(note_number, memo_password, df_status, df_supervisor):
    """التحقق من رقم المذكرة وكلمة السر"""
    # البحث في شيت حالة تسجيل المذكرات
    memo_status = df_status[df_status["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if not memo_status.empty:
        row = memo_status.iloc[0]
        # المذكرة موجودة مسبقًا
        if str(row.get("تم التسجيل", "")).strip() == "نعم" or str(row.get("الطالب الأول", "")).strip() != "":
            return False, None, "❌ هذه المذكرة مسجلة مسبقًا!"
    
    # البحث في شيت المذكرات - الأساتذة لكلمة السر
    supervisor_row = df_supervisor[df_supervisor["كلمة سر التسجيل"].astype(str).str.strip() == memo_password.strip()]
    if supervisor_row.empty:
        return False, None, "❌ كلمة السر غير صحيحة أو لا تخص هذا الأستاذ."
    
    # التأكد أن كلمة السر لم تستخدم مسبقًا
    row_s = supervisor_row.iloc[0]
    if str(row_s.get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ كلمة السر مستعملة مسبقًا!"
    
    return True, row_s, None

# ---------------------------
# تحديث جميع الشيتات بعد التسجيل
# ---------------------------
def update_registration(note_number, student1, student2=None):
    """تحديث شيت حالة المذكرات، الطلبة، المذكرات الأساتذة"""
    # تحميل البيانات مرة أخرى
    df_status = load_memos_status()
    df_supervisor = load_memos_supervisor()
    df_students = load_students()

    # --- تحديث شيت حالة تسجيل المذكرات ---
    row_idx = df_status[df_status["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if row_idx.empty:
        # إذا لم يوجد نضيفه في الصف الأول الفارغ
        idx = len(df_status) + 2
    else:
        idx = row_idx.index[0] + 2

    cols_status = df_status.columns.tolist()
    updates_status = [
        {"range": f"Feuille 1!{col_letter(cols_status.index('الطالب الأول')+1)}{idx}", "values": [[student1['اللقب'] + " " + student1['الإسم']]]},
        {"range": f"Feuille 1!{col_letter(cols_status.index('تم التسجيل')+1)}{idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{col_letter(cols_status.index('تاريخ التسجيل')+1)}{idx}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]},
        {"range": f"Feuille 1!{col_letter(cols_status.index('رقم المذكرة')+1)}{idx}", "values": [[note_number]]}
    ]
    if student2:
        updates_status.append({"range": f"Feuille 1!{col_letter(cols_status.index('الطالب الثاني')+1)}{idx}", "values": [[student2['اللقب'] + " " + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_STATUS_SHEET_ID,
        body={"valueInputOption":"USER_ENTERED", "data": updates_status}
    ).execute()

    # --- تحديث شيت الطلبة ---
    col_note = df_students.columns.tolist().index("رقم المذكرة")+1
    row_idx1 = df_students[df_students["اسم المستخدم"].str.strip() == student1['اسم المستخدم'].strip()].index[0]+2
    sheets_service.spreadsheets().values().update(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=f"Feuille 1!{col_letter(col_note)}{row_idx1}",
        valueInputOption="USER_ENTERED",
        body={"values":[[note_number]]}
    ).execute()

    if student2:
        row_idx2 = df_students[df_students["اسم المستخدم"].str.strip() == student2['اسم المستخدم'].strip()].index[0]+2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{col_letter(col_note)}{row_idx2}",
            valueInputOption="USER_ENTERED",
            body={"values":[[note_number]]}
        ).execute()

    # --- تحديث شيت المذكرات - الأساتذة ---
    supervisor_idx = df_supervisor[df_supervisor["كلمة سر التسجيل"].str.strip() == row_s["كلمة سر التسجيل"].strip()].index[0]+2
    cols_sup = df_supervisor.columns.tolist()
    updates_sup = [
        {"range": f"Feuille 1!{col_letter(cols_sup.index('الطالب الأول')+1)}{supervisor_idx}", "values": [[student1['اللقب'] + " " + student1['الإسم']]]},
        {"range": f"Feuille 1!{col_letter(cols_sup.index('تم التسجيل')+1)}{supervisor_idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{col_letter(cols_sup.index('تاريخ التسجيل')+1)}{supervisor_idx}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]},
        {"range": f"Feuille 1!{col_letter(cols_sup.index('رقم المذكرة')+1)}{supervisor_idx}", "values": [[note_number]]}
    ]
    if student2:
        updates_sup.append({"range": f"Feuille 1!{col_letter(cols_sup.index('الطالب الثاني')+1)}{supervisor_idx}", "values": [[student2['اللقب'] + " " + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SUPERVISOR_SHEET_ID,
        body={"valueInputOption":"USER_ENTERED", "data": updates_sup}
    ).execute()

# ---------------------------
# توليد PDF
# ---------------------------
def generate_pdf(note, memo, s1, s2=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"وصل تسجيل مذكرة الماستر", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial","",12)
    pdf.cell(0,10,f"رقم المذكرة: {note}", ln=True)
    pdf.cell(0,10,f"المشرف: {memo['الأستاذ']}", ln=True)
    pdf.cell(0,10,f"التخصص: {memo.get('التخصص','غير محدد')}", ln=True)
    pdf.ln(5)
    pdf.cell(0,10,f"الطالب الأول: {s1['اللقب']} {s1['الإسم']}", ln=True)
    if s2:
        pdf.cell(0,10,f"الطالب الثاني: {s2['اللقب']} {s2['الإسم']}", ln=True)
    pdf.ln(5)
    pdf.cell(0,10,f"تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    path = f"/tmp/memo_receipt_{note}.pdf"
    pdf.output(path)
    return path

# ---------------------------
# واجهة المستخدم
# ---------------------------
df_students = load_students()
df_status = load_memos_status()
df_supervisor = load_memos_supervisor()

if "logged" not in st.session_state:
    st.session_state.logged = False
    st.session_state.s1 = None
    st.session_state.s2 = None
    st.session_state.memo_type = "فردية"

# --- تسجيل الدخول ---
if not st.session_state.logged:
    st.markdown("## 🎓 تسجيل الدخول")
    st.session_state.memo_type = st.radio("نوع المذكرة", ["فردية","ثنائية"])
    u1 = st.text_input("اسم مستخدم الطالب الأول")
    p1 = st.text_input("كلمة السر", type="password")
    u2 = p2 = None
    if st.session_state.memo_type == "ثنائية":
        u2 = st.text_input("اسم مستخدم الطالب الثاني")
        p2 = st.text_input("كلمة السر", type="password")

    if st.button("تسجيل الدخول"):
        ok1, s1 = verify_student(u1, p1, df_students)
        if not ok1:
            st.error(s1)
            st.stop()
        s2 = None
        if st.session_state.memo_type == "ثنائية":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2:
                st.error(s2)
                st.stop()
        st.session_state.logged = True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.success(f"✅ تم تسجيل الدخول للطالب الأول: {s1['اللقب']} {s1['الإسم']}")
        if s2:
            st.success(f"✅ تم تسجيل الدخول للطالب الثاني: {s2['اللقب']} {s2['الإسم']}")

# --- تسجيل المذكرة بعد الدخول ---
else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    pwd = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد التسجيل"):
        ok, memo, err = verify_memo(note, pwd, df_status, df_supervisor)
        if not ok:
            st.error(err)
        else:
            update_registration(note, st.session_state.s1, st.session_state.s2)
            pdf_path = generate_pdf(note, memo, st.session_state.s1, st.session_state.s2)
            with open(pdf_path,"rb") as f:
                st.download_button("📄 تحميل وصل PDF", f, file_name=pdf_path.split("/")[-1])
            st.success(f"✅ تم تسجيل المذكرة بنجاح!\n👨‍🏫 المشرف: {memo['الأستاذ']}")