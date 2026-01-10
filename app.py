import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER

# Email
import smtplib
from email.mime.text import MIMEText

# --------------------------------------------------
# إعداد الصفحة
# --------------------------------------------------
st.set_page_config(
    page_title="تسجيل مذكرة الماستر",
    page_icon="🎓",
    layout="centered"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container {
    padding: 2rem;
    background-color: #1A2A3D;
    border-radius: 12px;
    max-width: 700px;
    margin: auto;
}
label, h1, h2, h3, h4, p, span { color: #ffffff !important; }
button {
    background-color: #256D85 !important;
    color: white !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Google Sheets
# --------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(
    st.secrets["service_account"],
    scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "YOUR_STUDENTS_SHEET_ID"
MEMOS_SHEET_ID = "YOUR_MEMOS_SHEET_ID"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"

# --------------------------------------------------
# أدوات مساعدة
# --------------------------------------------------
def col_letter(n):
    result = ""
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result

@st.cache_data(ttl=300)
def load_students():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=STUDENTS_RANGE
    ).execute().get("values", [])
    return pd.DataFrame(values[1:], columns=values[0])

@st.cache_data(ttl=300)
def load_memos():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_SHEET_ID,
        range=MEMOS_RANGE
    ).execute().get("values", [])
    return pd.DataFrame(values[1:], columns=values[0])

def verify_student(username, password, df):
    row = df[df["اسم المستخدم"].str.strip() == username.strip()]
    if row.empty:
        return False, "اسم المستخدم غير موجود"
    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "كلمة السر غير صحيحة"
    return True, row.iloc[0]

def student_has_memo(student):
    return str(student["رقم المذكرة"]).strip() != ""

def verify_memo(note_number, password, df):
    row = df[df["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if row.empty:
        return False, None, "رقم المذكرة غير موجود"
    memo = row.iloc[0]
    if memo["كلمة سر التسجيل"].strip() != password.strip():
        return False, None, "كلمة سر المذكرة غير صحيحة"
    if str(memo["تم التسجيل"]).strip() == "نعم":
        return False, None, "❌ المذكرة مسجلة مسبقًا"
    return True, memo, None

# --------------------------------------------------
# تحديث التسجيل
# --------------------------------------------------
def update_registration(note_number, student1, student2=None):
    memos = load_memos()
    idx = memos[memos["رقم المذكرة"].astype(str) == str(note_number)].index[0] + 2

    cols = memos.columns.tolist()
    updates = []

    updates.append({
        "range": f"Feuille 1!{col_letter(cols.index('الطالب الأول')+1)}{idx}",
        "values": [[student1["اللقب"] + " " + student1["الإسم"]]]
    })

    if student2 is not None:
        updates.append({
            "range": f"Feuille 1!{col_letter(cols.index('الطالب الثاني')+1)}{idx}",
            "values": [[student2["اللقب"] + " " + student2["الإسم"]]]
        })

    updates += [
        {
            "range": f"Feuille 1!{col_letter(cols.index('تم التسجيل')+1)}{idx}",
            "values": [["نعم"]]
        },
        {
            "range": f"Feuille 1!{col_letter(cols.index('تاريخ التسجيل')+1)}{idx}",
            "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]
        }
    ]

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

    students = load_students()
    col_note = col_letter(students.columns.tolist().index("رقم المذكرة")+1)

    for stt in [student1, student2]:
        if stt is not None:
            r = students[students["اسم المستخدم"] == stt["اسم المستخدم"]].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_note}{r}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

# --------------------------------------------------
# PDF
# --------------------------------------------------
def generate_pdf(note, memo, s1, s2=None):
    path = f"/tmp/وصل_مذكرة_{note}.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="C", alignment=TA_CENTER, fontSize=16))

    content = [
        Paragraph("جامعة محمد البشير الإبراهيمي<br/>كلية الحقوق والعلوم السياسية", styles["C"]),
        Spacer(1, 20),
        Paragraph("<b>وصل تسجيل مذكرة ماستر</b>", styles["Title"]),
        Spacer(1, 15),
        Paragraph(f"رقم المذكرة: {note}", styles["Normal"]),
        Paragraph(f"العنوان: {memo['عنوان المذكرة']}", styles["Normal"]),
        Paragraph(f"المشرف: {memo['الأستاذ']}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"الطالب: {s1['اللقب']} {s1['الإسم']}", styles["Normal"]),
    ]

    if s2 is not None:
        content.append(Paragraph(
            f"الطالب الثاني: {s2['اللقب']} {s2['الإسم']}", styles["Normal"]
        ))

    content.append(Spacer(1, 20))
    content.append(Paragraph(
        f"تاريخ التسجيل: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))

    doc.build(content)
    return path

# --------------------------------------------------
# Email
# --------------------------------------------------
def notify_supervisor(memo, note, s1, s2=None):
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]

    students = f"{s1['اللقب']} {s1['الإسم']}"
    if s2 is not None:
        students += f" و {s2['اللقب']} {s2['الإسم']}"

    body = f"""
تم تسجيل مذكرة ماستر بنجاح

رقم المذكرة: {note}
العنوان: {memo['عنوان المذكرة']}
الطلبة: {students}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "إشعار تسجيل مذكرة"
    msg["From"] = sender
    msg["To"] = memo["Email المشرف"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# --------------------------------------------------
# الواجهة
# --------------------------------------------------
df_students = load_students()
df_memos = load_memos()

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.markdown("## 🎓 تسجيل الدخول")
    memo_type = st.radio("نوع المذكرة", ["فردية", "ثنائية"])

    u1 = st.text_input("اسم المستخدم الطالب الأول")
    p1 = st.text_input("كلمة السر", type="password")

    if memo_type == "ثنائية":
        u2 = st.text_input("اسم المستخدم الطالب الثاني")
        p2 = st.text_input("كلمة السر الطالب الثاني", type="password")

    if st.button("دخول"):
        ok1, s1 = verify_student(u1, p1, df_students)
        if not ok1 or student_has_memo(s1):
            st.error("خطأ في الطالب الأول")
            st.stop()

        s2 = None
        if memo_type == "ثنائية":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2 or student_has_memo(s2):
                st.error("خطأ في الطالب الثاني")
                st.stop()

        st.session_state.logged = True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.session_state.memo_type = memo_type

else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    pwd = st.text_input("كلمة سر المذكرة", type="password")

    if st.button("تأكيد"):
        ok, memo, err = verify_memo(note, pwd, df_memos)
        if not ok:
            st.error(err)
            st.stop()

        update_registration(note, st.session_state.s1, st.session_state.s2)
        pdf = generate_pdf(note, memo, st.session_state.s1, st.session_state.s2)
        notify_supervisor(memo, note, st.session_state.s1, st.session_state.s2)

        with open(pdf, "rb") as f:
            st.download_button("📄 تحميل وصل PDF", f, file_name=pdf.split("/")[-1])

        st.success("✅ تم التسجيل بنجاح")
        st.cache_data.clear()