import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER

# Email
import smtplib
from email.mime.text import MIMEText

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(
    page_title="Master Memo Registration",
    page_icon="🎓",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
.block-container {
    padding: 2rem;
    background-color: #1A2A3D;
    border-radius: 12px;
    max-width: 700px;
    margin: auto;
}
label, h1, h2, h3, h4, p, span { color: #ffffff !important; }
button { background-color: #256D85 !important; color: white !important; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Google Sheets setup
# ---------------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(
    st.secrets["service_account"],
    scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "YOUR_STUDENTS_SHEET_ID"
MEMOS_SHEET_ID = "YOUR_MEMOS_SHEET_ID"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:K1000"

# ---------------------------
# Helper functions
# ---------------------------
def col_letter(n):
    """Convert column number to letter (for Sheets API)"""
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
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos():
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=MEMOS_SHEET_ID,
        range=MEMOS_RANGE
    ).execute().get("values", [])
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

def verify_student(username, password, df):
    row = df[df["اسم المستخدم"].str.strip() == username.strip()]
    if row.empty:
        return False, "❌ Username not found."
    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ Incorrect password."
    return True, row.iloc[0]

def student_has_memo(student):
    return str(student["رقم المذكرة"]).strip() != ""

def verify_memo(note_number, password, df):
    row = df[df["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if row.empty:
        return False, None, "❌ Memo number not found."
    memo = row.iloc[0]
    if memo["كلمة سر التسجيل"].strip() != password.strip():
        return False, None, "❌ This password does not belong to the supervisor for this memo."
    if str(memo["تم التسجيل"]).strip() == "نعم":
        return False, None, "❌ This password has already been used."
    return True, memo, None

# ---------------------------
# Update registration in Sheets
# ---------------------------
def update_registration(note_number, student1, student2=None):
    memos = load_memos()
    idx = memos[memos["رقم المذكرة"].astype(str) == str(note_number)].index[0] + 2

    cols = memos.columns.tolist()
    updates = []

    # Update students in memo
    updates.append({
        "range": f"Feuille 1!{col_letter(cols.index('الطالب الأول')+1)}{idx}",
        "values": [[student1["اللقب"] + " " + student1["الإسم"]]]
    })
    if student2 is not None:
        updates.append({
            "range": f"Feuille 1!{col_letter(cols.index('الطالب الثاني')+1)}{idx}",
            "values": [[student2["اللقب"] + " " + student2["الإسم"]]]
        })

    # Update registration flag and date
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

    # Update students sheet
    students = load_students()
    col_note = col_letter(students.columns.tolist().index("رقم المذكرة")+1)

    for stt in [student1, student2]:
        if stt is not None:
            r = students[students["اسم المستخدم"].astype(str).str.strip() == stt["اسم المستخدم"].strip()].index[0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{col_note}{r}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

# ---------------------------
# Generate PDF
# ---------------------------
def generate_pdf(note, memo, s1, s2=None):
    path = f"/tmp/memo_receipt_{note}.pdf"
    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="C", alignment=TA_CENTER, fontSize=16))

    content = [
        Paragraph("Université Mohamed B. El-Ibrahimi - Faculté de Droit et Science Politique", styles["C"]),
        Spacer(1, 20),
        Paragraph("<b>Master Memo Registration Receipt</b>", styles["Title"]),
        Spacer(1, 15),
        Paragraph(f"Memo Number: {note}", styles["Normal"]),
        Paragraph(f"Title: {memo['عنوان المذكرة']}", styles["Normal"]),
        Paragraph(f"Supervisor: {memo['الأستاذ']}", styles["Normal"]),
        Paragraph(f"Specialization: {memo.get('التخصص', 'Not specified')}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph(f"Student: {s1['اللقب']} {s1['الإسم']}", styles["Normal"]),
    ]
    if s2:
        content.append(Paragraph(f"Student 2: {s2['اللقب']} {s2['الإسم']}", styles["Normal"]))
    content.append(Spacer(1, 20))
    content.append(Paragraph(f"Registration Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))

    doc.build(content)
    return path

# ---------------------------
# Notify supervisor via email
# ---------------------------
def notify_supervisor(memo, note, s1, s2=None):
    sender = st.secrets["EMAIL_SENDER"]
    password = st.secrets["EMAIL_PASSWORD"]

    students = f"{s1['اللقب']} {s1['الإسم']}"
    if s2:
        students += f" and {s2['اللقب']} {s2['الإسم']}"

    body = f"""
A master memo has been successfully registered.

Memo Number: {note}
Title: {memo['عنوان المذكرة']}
Students: {students}
Supervisor: {memo['الأستاذ']}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Master Memo Registration Notification"
    msg["From"] = sender
    msg["To"] = memo["Email المشرف"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# ---------------------------
# Main UI
# ---------------------------
df_students = load_students()
df_memos = load_memos()

if "logged" not in st.session_state:
    st.session_state.logged = False

# --- Login page ---
if not st.session_state.logged:
    st.markdown("## 🎓 Login")
    memo_type = st.radio("Memo Type", ["Individual", "Group"])
    u1 = st.text_input("Student 1 Username")
    p1 = st.text_input("Password", type="password")
    u2 = p2 = None
    if memo_type == "Group":
        u2 = st.text_input("Student 2 Username")
        p2 = st.text_input("Student 2 Password", type="password")

    if st.button("Login"):
        ok1, s1 = verify_student(u1, p1, df_students)
        if not ok1:
            st.error(s1)
            st.stop()
        if student_has_memo(s1):
            st.error("❌ Student 1 already registered a memo!")
            st.stop()

        s2 = None
        if memo_type == "Group":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2:
                st.error(s2)
                st.stop()
            if student_has_memo(s2):
                st.error("❌ Student 2 already registered a memo!")
                st.stop()

        st.session_state.logged = True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.session_state.memo_type = memo_type

        st.success(f"✅ Login successful\n👤 Student 1: {s1['اللقب']} {s1['الإسم']}")
        if s2:
            st.success(f"👤 Student 2: {s2['اللقب']} {s2['الإسم']}")

# --- Memo registration page ---
else:
    st.markdown("## 📝 Register Memo")
    note = st.text_input("Memo Number")
    pwd = st.text_input("Supervisor Password", type="password")

    if st.button("Confirm Registration"):
        ok, memo, err = verify_memo(note, pwd, df_memos)
        if not ok:
            st.error(err)
            st.stop()

        # Update sheets
        update_registration(note, st.session_state.s1, st.session_state.s2)

        # Generate PDF
        pdf_path = generate_pdf(note, memo, st.session_state.s1, st.session_state.s2)

        # Notify supervisor
        notify_supervisor(memo, note, st.session_state.s1, st.session_state.s2)

        # Show PDF download
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download PDF Receipt", f, file_name=pdf_path.split("/")[-1])

        st.success(f"✅ Memo registered successfully!\n📄 Title: {memo['عنوان المذكرة']}\n👨‍🏫 Supervisor: {memo['الأستاذ']}\n📝 Specialization: {memo.get('التخصص', 'Not specified')}")