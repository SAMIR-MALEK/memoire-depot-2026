import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =========================
# إعداد الصفحة
# =========================
st.set_page_config(page_title="تسجيل مذكرة الماستر", page_icon="🎓", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: white; }
.block-container {
    background-color: #1A2A3D;
    padding: 2rem;
    border-radius: 12px;
    max-width: 700px;
    margin: auto;
}
label, h1, h2, h3, p { color: white !important; }
button {
    background-color: #256D85 !important;
    color: white !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Google API
# =========================
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
RANGE = "Feuille 1!A1:Z1000"

# =========================
# تحميل شيت الطلبة
# =========================
@st.cache_data
def load_students():
    result = sheets.spreadsheets().values().get(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=RANGE
    ).execute()
    values = result.get("values", [])

    columns = [
        "رقم البكالوريا","سنة البكالوريا","رقم التسجيل","اللقب","الإسم",
        "رقم المذكرة","التخصص","RFID","اسم المستخدم","كلمة السر","البريد المهني"
    ]

    df = pd.DataFrame(values[1:], columns=columns)
    return df.fillna("")

# =========================
# تحميل شيت المذكرات
# =========================
@st.cache_data
def load_memos():
    result = sheets.spreadsheets().values().get(
        spreadsheetId=MEMOS_SHEET_ID,
        range=RANGE
    ).execute()
    values = result.get("values", [])

    columns = [
        "الطالب الأول","الطالب الثاني","رقم المذكرة","عنوان المذكرة","التخصص",
        "الأستاذ","كلمة سر التسجيل","كلمة سر الإيداع",
        "تم التسجيل","تاريخ التسجيل","تم الإيداع","تاريخ الإيداع",
        "رئيسا","مناقشا"
    ]

    df = pd.DataFrame(values[1:], columns=columns)
    return df.fillna("")

df_students = load_students()
df_memos = load_memos()

# =========================
# العناوين
# =========================
st.markdown("<h3 style='text-align:center'>جامعة محمد البشير الإبراهيمي - برج بوعريريج</h3>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center'>كلية الحقوق والعلوم السياسية</h4>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center'>🎓 منصة تسجيل مذكرة الماستر</h2>", unsafe_allow_html=True)

st.markdown('<div class="block-container">', unsafe_allow_html=True)

# =========================
# اختيار النوع
# =========================
memo_type = st.radio("نوع المذكرة:", ["فردية", "ثنائية"])

username1 = st.text_input("اسم المستخدم – الطالب الأول")
password1 = st.text_input("كلمة السر – الطالب الأول", type="password")

if memo_type == "ثنائية":
    username2 = st.text_input("اسم المستخدم – الطالب الثاني")
    password2 = st.text_input("كلمة السر – الطالب الثاني", type="password")

# =========================
# تسجيل دخول الطلبة
# =========================
if st.button("تسجيل الدخول"):
    s1 = df_students[df_students["اسم المستخدم"] == username1]

    if s1.empty or s1.iloc[0]["كلمة السر"] != password1:
        st.error("❌ بيانات الطالب الأول غير صحيحة")
        st.stop()

    student1 = s1.iloc[0]

    if memo_type == "ثنائية":
        s2 = df_students[df_students["اسم المستخدم"] == username2]
        if s2.empty or s2.iloc[0]["كلمة السر"] != password2:
            st.error("❌ بيانات الطالب الثاني غير صحيحة")
            st.stop()
        student2 = s2.iloc[0]

    st.success("✅ تم تسجيل دخول الطلبة")

    # =========================
    # بيانات المذكرة
    # =========================
    note_number = st.text_input("رقم المذكرة")
    memo_password = st.text_input("كلمة سر التسجيل للمذكرة", type="password")

    if st.button("تأكيد تسجيل المذكرة"):
        memo = df_memos[df_memos["رقم المذكرة"] == note_number]

        if memo.empty:
            st.error("❌ رقم المذكرة غير موجود")
            st.stop()

        memo = memo.iloc[0]

        if memo["تم التسجيل"] == "نعم":
            st.error("❌ هذه المذكرة مسجلة مسبقًا")
            st.stop()

        if memo["كلمة سر التسجيل"] != memo_password:
            st.error("❌ كلمة سر المذكرة غير صحيحة")
            st.stop()

        st.info(f"📄 {memo['عنوان المذكرة']}")
        st.info(f"👨‍🏫 {memo['الأستاذ']}")

        idx = df_memos[df_memos["رقم المذكرة"] == note_number].index[0] + 2

        updates = [
            {
                "range": f"Feuille 1!A{idx}",
                "values": [[student1["اللقب"] + " " + student1["الإسم"]]]
            },
            {
                "range": f"Feuille 1!I{idx}",
                "values": [["نعم"]]
            },
            {
                "range": f"Feuille 1!J{idx}",
                "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]
            }
        ]

        if memo_type == "ثنائية":
            updates.insert(1, {
                "range": f"Feuille 1!B{idx}",
                "values": [[student2["اللقب"] + " " + student2["الإسم"]]]
            })

        sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()

        st.success("🎉 تم تسجيل المذكرة بنجاح")

st.markdown("</div>", unsafe_allow_html=True)
