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
credentials = Credentials.from_service_account_info(
    st.secrets["service_account"],
    scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)

# معرفات الشيتات
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
MEMOS_TEACHERS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
MEMOS_TEACHERS_RANGE = "Feuille 1!A1:L1000"

# ---------------------------
# دوال مساعدة
# ---------------------------
def col_letter(n):
    result = ""
    while n:
        n, r = divmod(n-1, 26)
        result = chr(65 + r) + result
    return result

@st.cache_data(ttl=300)
def load_students():
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=STUDENTS_RANGE
    ).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة الطلاب"); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos():
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_TEACHERS_SHEET_ID,
        range=MEMOS_TEACHERS_RANGE
    ).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في شيت المذكرات - الأساتذة"); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# ---------------------------
# التحقق من الطالب
# ---------------------------
def verify_student(username, password, df):
    row = df[df["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if row.empty:
        return False, "❌ اسم المستخدم غير موجود."
    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ كلمة السر غير صحيحة."
    return True, row.iloc[0]

def student_has_memo(student):
    return str(student["رقم المذكرة"]).strip() != ""

# ---------------------------
# التحقق من كلمة سر المذكرة
# ---------------------------
def verify_memo(note_number, password, df):
    row = df[df["كلمة سر التسجيل"].astype(str).str.strip() == password.strip()]
    if row.empty:
        return False, None, "❌ كلمة السر غير صحيحة."
    memo = row.iloc[0]
    if str(memo.get("تم التسجيل","")).strip() == "نعم":
        return False, None, "❌ هذه المذكرة مستعملة مسبقًا."
    return True, memo, None

# ---------------------------
# تحديث التسجيل
# ---------------------------
def update_registration(note_number, student1, student2=None):
    df_memos = load_memos()
    row_idx = df_memos[df_memos["كلمة سر التسجيل"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
    cols = df_memos.columns.tolist()
    updates = []

    updates.append({
        "range": f"Feuille 1!{col_letter(cols.index('الطالب الأول')+1)}{row_idx}",
        "values": [[student1["اللقب"] + " " + student1["الإسم"]]]
    })
    if student2:
        updates.append({
            "range": f"Feuille 1!{col_letter(cols.index('الطالب الثاني')+1)}{row_idx}",
            "values": [[student2["اللقب"] + " " + student2["الإسم"]]]
        })

    updates += [
        {
            "range": f"Feuille 1!{col_letter(cols.index('تم التسجيل')+1)}{row_idx}",
            "values": [["نعم"]]
        },
        {
            "range": f"Feuille 1!{col_letter(cols.index('تاريخ التسجيل')+1)}{row_idx}",
            "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]
        }
    ]

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_TEACHERS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

# ---------------------------
# توليد PDF بالعربية
# ---------------------------
def generate_pdf(note, memo, s1, s2=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)

    pdf.cell(0,10,"جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية",ln=True,align="C")
    pdf.ln(10)
    pdf.set_font('DejaVu','B',16)
    pdf.cell(0,10,"وصل تسجيل مذكرة الماستر",ln=True,align="C")
    pdf.ln(10)
    pdf.set_font('DejaVu','',12)

    pdf.cell(0,10,f"رقم المذكرة: {note}",ln=True)
    pdf.cell(0,10,f"عنوان المذكرة: {memo['رقم المذكرة']}",ln=True)
    pdf.cell(0,10,f"المشرف: {memo['الأستاذ']}",ln=True)
    pdf.cell(0,10,f"الطالب الأول: {s1['اللقب']} {s1['الإسم']}",ln=True)
    if s2:
        pdf.cell(0,10,f"الطالب الثاني: {s2['اللقب']} {s2['الإسم']}",ln=True)
    pdf.cell(0,10,f"تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d %H:%M')}",ln=True)

    path = f"/tmp/memo_receipt_{note}.pdf"
    pdf.output(path)
    return path

# ---------------------------
# واجهة المستخدم
# ---------------------------
df_students = load_students()
df_memos = load_memos()

if "logged" not in st.session_state:
    st.session_state.logged = False

# تسجيل الدخول
if not st.session_state.logged:
    st.markdown("## 🎓 تسجيل الدخول")
    memo_type = st.radio("نوع المذكرة", ["فردية","ثنائية"])
    u1 = st.text_input("اسم مستخدم الطالب الأول")
    p1 = st.text_input("كلمة السر", type="password")
    u2 = p2 = None
    if memo_type == "ثنائية":
        u2 = st.text_input("اسم مستخدم الطالب الثاني")
        p2 = st.text_input("كلمة السر", type="password")

    if st.button("تسجيل الدخول"):
        ok1, s1 = verify_student(u1,p1,df_students)
        if not ok1: st.error(s1); st.stop()
        if student_has_memo(s1): st.error("❌ الطالب الأول سجل مذكرة من قبل!"); st.stop()
        s2 = None
        if memo_type=="ثنائية":
            ok2, s2 = verify_student(u2,p2,df_students)
            if not ok2: st.error(s2); st.stop()
            if student_has_memo(s2): st.error("❌ الطالب الثاني سجل مذكرة من قبل!"); st.stop()
        st.session_state.logged=True
        st.session_state.s1=s1
        st.session_state.s2=s2
        st.session_state.memo_type=memo_type
        st.success(f"✅ تم تسجيل الدخول: {s1['اللقب']} {s1['الإسم']}")
        if s2: st.success(f"✅ الطالب الثاني: {s2['اللقب']} {s2['الإسم']}")

# تسجيل المذكرة
else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    pwd = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد التسجيل"):
        ok, memo, err = verify_memo(note, pwd, df_memos)
        if not ok: st.error(err); st.stop()
        update_registration(note, st.session_state.s1, st.session_state.s2)
        pdf_path = generate_pdf(note, memo, st.session_state.s1, st.session_state.s2)
        with open(pdf_path,"rb") as f:
            st.download_button("📄 تحميل وصل PDF", f, file_name=f"memo_{note}.pdf")
        st.success(f"✅ تم تسجيل المذكرة بنجاح!\n👨‍🏫 المشرف: {memo['الأستاذ']}")