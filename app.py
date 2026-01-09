import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ================= CONFIG =================
st.set_page_config(page_title="منصة تسجيل المذكرات", layout="centered")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CREDS = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=CREDS)
sheets = service.spreadsheets().values()

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"

# ================= LOAD DATA =================
@st.cache_data
def load_students():
    res = sheets.get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
    values = res.get("values", [])

    columns = [
        "رقم البكالوريا","سنة البكالوريا","رقم التسجيل","اللقب","الإسم",
        "رقم المذكرة","التخصص","RFID","اسم المستخدم","كلمة السر","البريد المهني"
    ]

    data = []
    for row in values[1:]:
        row = row[:11] + [""] * (11 - len(row))
        data.append(row)

    return pd.DataFrame(data, columns=columns)

@st.cache_data
def load_memos():
    res = sheets.get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
    values = res.get("values", [])

    columns = [
        "الطالب الأول","الطالب الثاني","رقم المذكرة","عنوان المذكرة","التخصص",
        "الأستاذ","كلمة سر التسجيل","كلمة سر الإيداع",
        "تم التسجيل","تاريخ التسجيل","تم الإيداع","تاريخ الإيداع",
        "رئيسا","مناقشا"
    ]

    data = []
    for row in values[1:]:
        row = row[:14] + [""] * (14 - len(row))
        data.append(row)

    return pd.DataFrame(data, columns=columns)

students_df = load_students()
memos_df = load_memos()

# ================= UI =================
st.markdown(
"""
<h4 style='text-align:center'>
جامعة محمد البشير الإبراهيمي – برج بوعريريج<br>
كلية الحقوق والعلوم السياسية
</h4>
<h2 style='text-align:center'>🎓 منصة تسجيل مذكرة الماستر</h2>
""",
unsafe_allow_html=True
)

# ================= LOGIN =================
st.subheader("🔐 تسجيل دخول الطلبة")

memo_type = st.radio("نوع المذكرة", ["فردية", "ثنائية"])

def student_login(label):
    with st.expander(label):
        username = st.text_input("اسم المستخدم", key=label+"u")
        password = st.text_input("كلمة السر", type="password", key=label+"p")
        return username, password

u1, p1 = student_login("الطالب الأول")
u2 = p2 = None

if memo_type == "ثنائية":
    u2, p2 = student_login("الطالب الثاني")

if st.button("دخول"):
    s1 = students_df[
        (students_df["اسم المستخدم"] == u1) &
        (students_df["كلمة السر"] == p1)
    ]

    if s1.empty:
        st.error("بيانات الطالب الأول غير صحيحة")
        st.stop()

    student1 = s1.iloc[0]

    if student1["رقم المذكرة"]:
        st.error("الطالب الأول مسجل سابقًا")
        st.stop()

    student2 = None
    if memo_type == "ثنائية":
        s2 = students_df[
            (students_df["اسم المستخدم"] == u2) &
            (students_df["كلمة السر"] == p2)
        ]

        if s2.empty:
            st.error("بيانات الطالب الثاني غير صحيحة")
            st.stop()

        student2 = s2.iloc[0]

        if student2["رقم المذكرة"]:
            st.error("الطالب الثاني مسجل سابقًا")
            st.stop()

    st.session_state["student1"] = student1.to_dict()
    st.session_state["student2"] = student2.to_dict() if student2 is not None else None
    st.session_state["stage"] = "register"

# ================= REGISTER MEMO =================
if st.session_state.get("stage") == "register":
    st.divider()
    st.subheader("📄 تسجيل المذكرة")

    memo_number = st.text_input("رقم المذكرة")
    memo_password = st.text_input("كلمة سر التسجيل", type="password")

    if st.button("تأكيد التسجيل"):
        memo = memos_df[
            (memos_df["رقم المذكرة"] == memo_number) &
            (memos_df["كلمة سر التسجيل"] == memo_password)
        ]

        if memo.empty:
            st.error("رقم المذكرة أو كلمة السر خاطئة")
            st.stop()

        memo = memo.iloc[0]

        if memo["تم التسجيل"] == "نعم":
            st.error("هذه المذكرة مسجلة سابقًا")
            st.stop()

        st.success("تم التحقق من المذكرة")

        st.write("**عنوان المذكرة:**", memo["عنوان المذكرة"])
        st.write("**المشرف:**", memo["الأستاذ"])

        if st.button("تسجيل نهائي"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            row_idx = memos_df[memos_df["رقم المذكرة"] == memo_number].index[0] + 2

            updates = [
                {"range": f"Feuille 1!A{row_idx}", "values": [[
                    st.session_state["student1"]["اللقب"] + " " +
                    st.session_state["student1"]["الإسم"]
                ]]},
                {"range": f"Feuille 1!B{row_idx}", "values": [[
                    st.session_state["student2"]["اللقب"] + " " +
                    st.session_state["student2"]["الإسم"]
                    if st.session_state["student2"] else ""
                ]]},
                {"range": f"Feuille 1!I{row_idx}", "values": [["نعم"]]},
                {"range": f"Feuille 1!J{row_idx}", "values": [[now]]},
            ]

            sheets.batchUpdate(
                spreadsheetId=MEMOS_SHEET_ID,
                body={"valueInputOption": "RAW", "data": updates}
            ).execute()

            # تحديث الطلبة
            for s in [st.session_state["student1"], st.session_state["student2"]]:
                if s:
                    idx = students_df[
                        students_df["رقم التسجيل"] == s["رقم التسجيل"]
                    ].index[0] + 2

                    sheets.update(
                        spreadsheetId=STUDENTS_SHEET_ID,
                        range=f"Feuille 1!F{idx}",
                        valueInputOption="RAW",
                        body={"values": [[memo_number]]}
                    ).execute()

            st.success("🎉 تم تسجيل المذكرة بنجاح")
            st.stop()
