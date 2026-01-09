import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرة الماستر", page_icon="🎓", layout="centered")

# CSS للواجهة الزرقاء الليلية
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  {
    font-family: 'Cairo', sans-serif !important;
}
.main {
    background-color: #0A1B2C;
    color: #ffffff;
}
.block-container {
    padding: 2rem;
    background-color: #1A2A3D;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    max-width: 700px;
    margin: auto;
}
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label {
    color: #ffffff !important;
}
input, button, select {
    font-size: 16px !important;
}
button {
    background-color: #256D85 !important;
    color: white !important;
    border: none !important;
    padding: 10px 20px !important;
    border-radius: 6px !important;
    transition: background-color 0.3s ease;
}
button:hover {
    background-color: #2C89A0 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- إعداد الاتصال بـ Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

# ---------------- Google Sheets IDs ----------------
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
STUDENTS_RANGE = "Feuille 1!A1:Z1000"
MEMOS_RANGE = "Feuille 1!A1:Z1000"

# ---------------- تحميل بيانات الطلاب ----------------
@st.cache_data(ttl=300)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات في شيت الطلاب.")
            st.stop()
        columns = values[0]
        df = pd.DataFrame(values[1:], columns=columns)
        df = df.reindex(columns=columns).fillna("")  # تأكد من جميع الأعمدة
        return df
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات الطلاب: {e}")
        st.stop()

# ---------------- تحميل بيانات المذكرات ----------------
@st.cache_data(ttl=300)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID,
            range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات في شيت المذكرات.")
            st.stop()
        columns = ["الطالب الأول","الطالب الثاني","رقم المذكرة","عنوان المذكرة","التخصص","الأستاذ",
                   "كلمة سر التسجيل","كلمة سر الإيداع","تم التسجيل","تاريخ التسجيل","تم الإيداع","تاريخ الإيداع",
                   "رئيسا","مناقشا"]
        df = pd.DataFrame(values[1:], columns=columns)
        df = df.reindex(columns=columns).fillna("")
        return df
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات المذكرات: {e}")
        st.stop()

# ---------------- التحقق من الطالب ----------------
def verify_student(username, password, df_students):
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if student.empty:
        return False, "اسم المستخدم غير موجود."
    if student.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "كلمة السر غير صحيحة."
    return True, student.iloc[0]

# ---------------- التحقق من المذكرة ----------------
def verify_memo(note_number, memo_password, df_memos):
    memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo.empty:
        return False, None, "رقم المذكرة غير موجود."
    if memo.iloc[0]["كلمة سر التسجيل"].strip() != memo_password.strip():
        return False, None, "كلمة سر المذكرة غير صحيحة."
    if memo.iloc[0]["تم التسجيل"].strip().lower() == "نعم":
        return False, None, "❌ المذكرة مسجلة مسبقًا."
    return True, memo.iloc[0], None

# ---------------- تحديث حالة التسجيل في شيت المذكرات ----------------
def update_memo_registration(note_number, student1, student2=None):
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID,
            range=MEMOS_RANGE
        ).execute()
        values = result.get('values', [])
        columns = ["الطالب الأول","الطالب الثاني","رقم المذكرة","عنوان المذكرة","التخصص","الأستاذ",
                   "كلمة سر التسجيل","كلمة سر الإيداع","تم التسجيل","تاريخ التسجيل","تم الإيداع","تاريخ الإيداع",
                   "رئيسا","مناقشا"]
        df = pd.DataFrame(values[1:], columns=columns)
        df = df.reindex(columns=columns).fillna("")
        row_idx = df[df["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index
        if row_idx.empty:
            st.error("❌ رقم المذكرة غير موجود أثناء التحديث.")
            return False
        idx = row_idx[0] + 2  # +2 بسبب رأس الجدول و1-based index
        student1_col = columns.index("الطالب الأول") + 1
        updates = [
            {"range": f"Feuille 1!{chr(64+student1_col)}{idx}", "values": [[student1['اللقب'] + " " + student1['الإسم']]]]},
            {"range": f"Feuille 1!I{idx}", "values": [["نعم"]]},  # تم التسجيل
            {"range": f"Feuille 1!J{idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}  # تاريخ التسجيل
        ]
        if student2 is not None:
            student2_col = columns.index("الطالب الثاني") + 1
            updates.append({"range": f"Feuille 1!{chr(64+student2_col)}{idx}", "values": [[student2['اللقب'] + " " + student2['الإسم']]]})
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMOS_SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": updates}
        ).execute()
        return True
    except Exception as e:
        st.error(f"❌ فشل تحديث حالة التسجيل: {e}")
        return False

# ---------------- تحديث شيت الطلاب برقم المذكرة ----------------
def update_student_memo_number(student, note_number):
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=STUDENTS_RANGE
        ).execute()
        values = result.get('values', [])
        columns = values[0]
        df = pd.DataFrame(values[1:], columns=columns)
        df = df.reindex(columns=columns).fillna("")
        row_idx = df[df["اسم المستخدم"].astype(str).str.strip() == student["اسم المستخدم"].strip()].index
        if row_idx.empty:
            st.warning(f"⚠️ الطالب {student['الإسم']} غير موجود في شيت الطلاب أثناء التحديث.")
            return False
        idx = row_idx[0] + 2
        memo_col = columns.index("رقم المذكرة") + 1
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{chr(64+memo_col)}{idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[note_number]]}
        ).execute()
        return True
    except Exception as e:
        st.error(f"❌ فشل تحديث شيت الطلاب: {e}")
        return False

# ---------------- تحميل البيانات ----------------
df_students = load_students()
df_memos = load_memos()

# ---------------- صندوق التسجيل ----------------
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;color:white;'>جامعة محمد البشير الإبراهيمي - برج بوعريريج</h3>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;color:white;'>كلية الحقوق والعلوم السياسية</h3>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;color:white;'>🎓 منصة تسجيل مذكرة الماستر</h2>", unsafe_allow_html=True)

# اختيار نوع المذكرة
memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])

# حقول الطلاب
username1 = st.text_input("اسم المستخدم للطالب 1 (استعمل معلومات موودل)")
password1 = st.text_input("كلمة السر للطالب 1 (استعمل معلومات موودل)", type="password")
username2 = password2 = None
if memo_type == "ثنائية":
    username2 = st.text_input("اسم المستخدم للطالب 2 (استعمل معلومات موودل)")
    password2 = st.text_input("كلمة السر للطالب 2 (استعمل معلومات موودل)", type="password")

# ---------------- تسجيل الدخول والتحقق ----------------
if st.button("تسجيل الدخول"):
    valid1, student1 = verify_student(username1, password1, df_students)
    if not valid1:
        st.error(f"الطالب 1: {student1}")
    else:
        student2 = None
        if memo_type == "ثنائية":
            valid2, student2 = verify_student(username2, password2, df_students)
            if not valid2:
                st.error(f"الطالب 2: {student2}")
        if memo_type == "فردية" or (memo_type == "ثنائية" and valid2):
            st.success(f"✅ تم تسجيل الدخول للطالب/الطلاب: {student1['الإسم']}" + (f" و {student2['الإسم']}" if student2 else ""))

            # إدخال بيانات المذكرة
            note_number = st.text_input("رقم المذكرة")
            memo_password = st.text_input("كلمة سر المذكرة", type="password")

            if st.button("موافق على التسجيل"):
                valid_memo, memo_info, error_msg = verify_memo(note_number, memo_password, df_memos)
                if not valid_memo:
                    st.error(error_msg)
                else:
                    st.info(f"📄 عنوان المذكرة: {memo_info['عنوان المذكرة']}")
                    st.info(f"👨‍🏫 المشرف: {memo_info['الأستاذ']}")

                    # تحديث شيت المذكرات
                    updated_memo = update_memo_registration(note_number, student1, student2)
                    # تحديث شيت الطلاب
                    updated_student1 = update_student_memo_number(student1, note_number)
                    if student2:
                        updated_student2 = update_student_memo_number(student2, note_number)

                    if updated_memo:
                        st.success("✅ تم تسجيل المذكرة بنجاح وتم تحديث الشيت بنجاح!")

st.markdown('</div>', unsafe_allow_html=True)
