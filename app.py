import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText

# ---------------------------
# إعداد الصفحة
# ---------------------------
st.set_page_config(page_title="تسجيل مذكرة الماستر", page_icon="🎓", layout="centered")

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

# --- معرفات الشيتات
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
STATE_MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
SUPERVISOR_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
STATE_MEMOS_RANGE = "Feuille 1!A1:N1000"
SUPERVISOR_MEMOS_RANGE = "Feuille 1!A1:K1000"

# ---------------------------
# تحميل بيانات الطلبة والمذكرات
# ---------------------------
@st.cache_data(ttl=300)
def load_students():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=STUDENTS_RANGE
    ).execute().get("values", [])
    if not values:
        st.error("❌ لا توجد بيانات في شيت الطلبة")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_state_memos():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=STATE_MEMOS_SHEET_ID,
        range=STATE_MEMOS_RANGE
    ).execute().get("values", [])
    if not values:
        st.error("❌ لا توجد بيانات في شيت حالة تسجيل المذكرات")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_supervisor_memos():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=SUPERVISOR_MEMOS_SHEET_ID,
        range=SUPERVISOR_MEMOS_RANGE
    ).execute().get("values", [])
    if not values:
        st.error("❌ لا توجد بيانات في شيت المذكرات الأساتذة")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# ---------------------------
# التحقق من بيانات الطالب
# ---------------------------
def verify_student(username, password, df):
    student = df[df["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if student.empty:
        return False, "❌ اسم المستخدم غير موجود."
    if student.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ كلمة السر غير صحيحة."
    if str(student.iloc[0]["رقم المذكرة"]).strip() != "":
        return False, "❌ هذا الطالب سجل مذكرة من قبل!"
    return True, student.iloc[0]

# ---------------------------
# التحقق من المذكرة قبل التسجيل
# ---------------------------
def verify_memo(note_number, memo_password, df_state, df_supervisor):
    # --- الخطوة 1: شيت حالة تسجيل المذكرات ---
    memo_state = df_state[df_state["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if not memo_state.empty:
        row = memo_state.iloc[0]
        if str(row["تم التسجيل"]).strip() == "نعم" or str(row["الطالب الأول"]).strip() != "":
            return False, None, "❌ هذه المذكرة محجوزة مسبقًا."
        supervisor_name = row["الأستاذ"]
    else:
        supervisor_name = None

    # --- الخطوة 2: شيت المذكرات الأساتذة ---
    df_sup_filtered = df_supervisor[df_supervisor["الأستاذ"].astype(str).str.strip() == supervisor_name]
    memo_sup = df_sup_filtered[df_sup_filtered["كلمة سر التسجيل"].astype(str).str.strip() == memo_password.strip()]
    if memo_sup.empty:
        return False, None, "❌ كلمة السر غير صحيحة أو مستعملة."
    row_sup = memo_sup.iloc[0]
    if str(row_sup.get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ كلمة السر هذه مستعملة مسبقًا."

    return True, {"supervisor": supervisor_name}, None

# ---------------------------
# تحديث المذكرات بعد التسجيل
# ---------------------------
def update_registration(note_number, student1, student2=None):
    df_state = load_state_memos()
    df_supervisor = load_supervisor_memos()

    # --- تحديث شيت حالة التسجيل ---
    idx_state = df_state[df_state["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index
    if idx_state.empty:
        idx_state = [len(df_state)]  # إذا الرقم جديد، أضف سطر جديد
    row_state = idx_state[0] + 2  # جوجل شيت يبدأ من الصف 2

    updates_state = [
        {"range": f"Feuille 1!A{row_state}", "values": [[student1["اللقب"] + " " + student1["الإسم"]]]},
        {"range": f"Feuille 1!B{row_state}", "values": [[student2["اللقب"] + " " + student2["الإسم"]] if student2 else [""]]},
        {"range": f"Feuille 1!C{row_state}", "values": [[note_number]]},
        {"range": f"Feuille 1!J{row_state}", "values": [["نعم"]]},  # تم التسجيل
        {"range": f"Feuille 1!K{row_state}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]}
    ]

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=STATE_MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates_state}
    ).execute()

    # --- تحديث شيت المذكرات الأساتذة ---
    df_sup_filtered = df_supervisor[df_supervisor["الأستاذ"].astype(str).str.strip() == student1["التخصص"]]  # استخدم supervisor المناسب
    idx_sup = df_supervisor[df_supervisor["كلمة سر التسجيل"].astype(str).str.strip() == memo_password.strip()].index[0] + 2
    updates_sup = [
        {"range": f"Feuille 1!A{idx_sup}", "values": [[student1["اللقب"] + " " + student1["الإسم"]]]},
        {"range": f"Feuille 1!B{idx_sup}", "values": [[student2["اللقب"] + " " + student2["الإسم"]] if student2 else [""]]},
        {"range": f"Feuille 1!C{idx_sup}", "values": [[note_number]]},
        {"range": f"Feuille 1!F{idx_sup}", "values": [["نعم"]]},
        {"range": f"Feuille 1!G{idx_sup}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]}
    ]
    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=SUPERVISOR_MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates_sup}
    ).execute()

    # --- تحديث شيت الطلبة ---
    df_students = load_students()
    col_note = df_students.columns.tolist().index("رقم المذكرة") + 1

    for stt in [student1, student2]:
        if stt is not None:
            r = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == stt["اسم المستخدم"].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{chr(64+col_note)}{r}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

# ---------------------------
# توليد PDF (FPDF)
# ---------------------------
def generate_pdf(note, s1, s2=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "جامعة محمد البشير الإبراهيمي - كلية الحقوق والعلوم السياسية", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "وصل تسجيل مذكرة الماستر", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"رقم المذكرة: {note}", ln=True)
    pdf.cell(0, 10, f"الطالب الأول: {s1['اللقب']} {s1['الإسم']}", ln=True)
    if s2:
        pdf.cell(0, 10, f"الطالب الثاني: {s2['اللقب']} {s2['الإسم']}", ln=True)
    pdf.cell(0, 10, f"تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    path = f"/tmp/memo_receipt_{note}.pdf"
    pdf.output(path)
    return path

# ---------------------------
# واجهة المستخدم
# ---------------------------
df_students = load_students()
df_state = load_state_memos()
df_supervisor = load_supervisor_memos()

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.markdown("## 🎓 تسجيل الدخول")
    memo_type = st.radio("نوع المذكرة", ["فردية", "ثنائية"])
    u1 = st.text_input("اسم مستخدم الطالب الأول")
    p1 = st.text_input("كلمة السر", type="password")
    u2 = p2 = None
    if memo_type == "ثنائية":
        u2 = st.text_input("اسم مستخدم الطالب الثاني")
        p2 = st.text_input("كلمة السر", type="password")

    if st.button("تسجيل الدخول"):
        ok1, s1 = verify_student(u1, p1, df_students)
        if not ok1: st.error(s1); st.stop()
        s2 = None
        if memo_type == "ثنائية":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2: st.error(s2); st.stop()
        st.session_state.logged = True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.session_state.memo_type = memo_type
        st.success(f"✅ تم تسجيل الدخول للطالب: {s1['الإسم']}")
        if s2: st.success(f"✅ تم تسجيل الدخول للطالب: {s2['الإسم']}")

else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    memo_password = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد التسجيل"):
        valid, info, err = verify_memo(note, memo_password, df_state, df_supervisor)
        if not valid:
            st.error(err)
        else:
            update_registration(note, st.session_state.s1, st.session_state.s2)
            pdf_path = generate_pdf(note, st.session_state.s1, st.session_state.s2)
            with open(pdf_path, "rb") as f:
                st.download_button("📄 تحميل وصل PDF", f, file_name=pdf_path.split("/")[-1])
            st.success("✅ تم تسجيل المذكرة بنجاح!")