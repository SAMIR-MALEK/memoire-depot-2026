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
st.set_page_config(page_title="تسجيل مذكرة الماستر", page_icon="🎓", layout="centered")

# CSS للواجهة
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Cairo', sans-serif !important; }
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
MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"

# ---------------------------
# دوال مساعدة
# ---------------------------
def load_students():
    """تحميل بيانات الطلاب من Google Sheets"""
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=STUDENTS_RANGE
    ).execute()
    values = result.get('values', [])
    if not values:
        st.error("❌ لا توجد بيانات في صفحة الطلاب.")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def load_memos():
    """تحميل بيانات المذكرات من Google Sheets"""
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_SHEET_ID,
        range=MEMOS_RANGE
    ).execute()
    values = result.get('values', [])
    if not values:
        st.error("❌ لا توجد بيانات في صفحة المذكرات.")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def verify_student(username, password, df_students):
    """التحقق من اسم المستخدم وكلمة السر"""
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if student.empty:
        return False, "❌ اسم المستخدم غير موجود."
    if student.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ كلمة السر غير صحيحة."
    return True, student.iloc[0]

def student_already_registered(student):
    """التحقق إذا سجل الطالب مذكرة من قبل"""
    return str(student['رقم المذكرة']).strip() != ""

def verify_memo(note_number, memo_password, df_memos):
    """التحقق من رقم المذكرة وكلمة سر الأستاذ"""
    memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo.empty:
        return False, None, "❌ رقم المذكرة غير موجود."
    memo_row = memo.iloc[0]
    if memo_row["كلمة سر التسجيل"].strip() != memo_password.strip():
        return False, None, "❌ كلمة سر المذكرة غير صحيحة."
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ هذه المذكرة مسجلة مسبقًا!"
    return True, memo_row, None

def col_letter(n):
    """تحويل رقم العمود إلى حرف لاستخدامه في Google Sheets"""
    result = ""
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result

def update_memo_registration(note_number, student1, student2=None):
    """تحديث شيت المذكرات وشيت الطلاب بعد التسجيل"""
    df_memos = load_memos()
    idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2

    cols = df_memos.columns.tolist()
    updates = [
        {"range": f"Feuille 1!{col_letter(cols.index('الطالب الأول')+1)}{idx}", "values": [[student1['اللقب']+' '+student1['الإسم']]]},
        {"range": f"Feuille 1!{col_letter(cols.index('تم التسجيل')+1)}{idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{col_letter(cols.index('تاريخ التسجيل')+1)}{idx}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]}
    ]
    if student2:
        updates.append({"range": f"Feuille 1!{col_letter(cols.index('الطالب الثاني')+1)}{idx}", "values": [[student2['اللقب']+' '+student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

    # تحديث رقم المذكرة في شيت الطلاب
    df_students = load_students()
    col_note = col_letter(df_students.columns.tolist().index("رقم المذكرة")+1)
    for stt in [student1, student2]:
        if stt:
            row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip()==stt["اسم المستخدم"].strip()].index[0]+2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_note}{row_idx}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

def generate_pdf(note, memo, s1, s2=None):
    """توليد PDF للوصول"""
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
    pdf.cell(0, 10, f"عنوان المذكرة: {memo['عنوان المذكرة']}", ln=True)
    pdf.cell(0, 10, f"المشرف: {memo['الأستاذ']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"الطالب الأول: {s1['اللقب']} {s1['الإسم']}", ln=True)
    if s2:
        pdf.cell(0, 10, f"الطالب الثاني: {s2['اللقب']} {s2['الإسم']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
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

if not st.session_state.logged:
    st.markdown("## 🎓 تسجيل الدخول")
    memo_type = st.radio("نوع المذكرة", ["فردية", "ثنائية"])
    u1 = st.text_input("اسم مستخدم الطالب الأول")
    p1 = st.text_input("كلمة السر", type="password")
    u2 = p2 = None
    if memo_type=="ثنائية":
        u2 = st.text_input("اسم مستخدم الطالب الثاني")
        p2 = st.text_input("كلمة السر", type="password")

    if st.button("تسجيل الدخول"):
        ok1, s1 = verify_student(u1, p1, df_students)
        if not ok1:
            st.error(s1)
            st.stop()
        if student_already_registered(s1):
            st.error("❌ الطالب الأول سجل مذكرة من قبل!")
            st.stop()

        s2=None
        if memo_type=="ثنائية":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2:
                st.error(s2)
                st.stop()
            if student_already_registered(s2):
                st.error("❌ الطالب الثاني سجل مذكرة من قبل!")
                st.stop()

        st.session_state.logged=True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.session_state.memo_type = memo_type

        st.success(f"✅ تسجيل الدخول ناجح\n👤 الطالب الأول: {s1['اللقب']} {s1['الإسم']}")
        if s2:
            st.success(f"👤 الطالب الثاني: {s2['اللقب']} {s2['الإسم']}")

else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    pwd = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد التسجيل"):
        ok, memo, err = verify_memo(note, pwd, df_memos)
        if not ok:
            st.error(err)
            st.stop()
        update_memo_registration(note, st.session_state.s1, st.session_state.s2)
        pdf_path = generate_pdf(note, memo, st.session_state.s1, st.session_state.s2)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 تحميل وصل PDF", f, file_name=pdf_path.split("/")[-1])
        st.success(f"✅ تم تسجيل المذكرة بنجاح!\n📄 العنوان: {memo['عنوان المذكرة']}\n👨‍🏫 المشرف: {memo['الأستاذ']}")