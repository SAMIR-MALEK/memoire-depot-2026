import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعداد الصفحة
st.set_page_config(page_title="تسجيل مذكرة الماستر", page_icon="🎓", layout="centered")

# CSS للواجهة
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); max-width: 700px; margin: auto; }
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color: #ffffff !important; }
input, button, select { font-size: 16px !important; }
button { background-color: #256D85 !important; color: white !important; border: none !important; padding: 10px 20px !important; border-radius: 6px !important; transition: background-color 0.3s ease; }
button:hover { background-color: #2C89A0 !important; }
</style>
""", unsafe_allow_html=True)

# --- اتصال Google Sheets ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
MEMOS_RANGE = "Feuille 1!A1:N1000"
STUDENTS_RANGE = "Feuille 1!A1:K1000"

# --- تحميل البيانات ---
@st.cache_data(ttl=300)
def load_students():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في شيت الطلاب."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في شيت المذكرات."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# --- التحقق من الطالب ---
def verify_student(username, password, df_students):
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if student.empty: return False, "اسم المستخدم غير موجود."
    if student.iloc[0]["كلمة السر"].strip() != password.strip(): return False, "كلمة السر غير صحيحة."
    return True, student.iloc[0]

def check_student_already_registered(student):
    return str(student['رقم المذكرة']).strip() != ""

# --- التحقق من المذكرة مع منع إعادة التسجيل ---
def verify_memo(note_number, memo_password, df_memos):
    memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo.empty:
        return False, None, "رقم المذكرة غير موجود."
    memo_row = memo.iloc[0]

    # التحقق من كلمة السر
    if memo_row["كلمة سر التسجيل"].strip() != memo_password.strip():
        return False, None, "كلمة سر المذكرة غير صحيحة."
    
    # التحقق من حالة التسجيل
    if str(memo_row.get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ هذه المذكرة مسجلة بالفعل ولا يمكن تسجيلها مرة ثانية!"
    
    return True, memo_row, None

# --- تحديث التسجيل ---
def update_memo_registration(note_number, student1, student2=None):
    # تحديث شيت المذكرات
    result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
    values = result.get('values', [])
    df_memos = pd.DataFrame(values[1:], columns=values[0])
    row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index
    if row_idx.empty: st.error("❌ رقم المذكرة غير موجود أثناء التحديث."); return False
    idx = row_idx[0] + 2

    col_names = df_memos.columns.tolist()
    student1_col = col_names.index("الطالب الأول") + 1
    student2_col = col_names.index("الطالب الثاني") + 1
    registered_col = col_names.index("تم التسجيل") + 1
    date_col = col_names.index("تاريخ التسجيل") + 1

    data = [
        {"range": f"Feuille 1!{chr(64+student1_col)}{idx}", "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
        {"range": f"Feuille 1!{chr(64+registered_col)}{idx}", "values": [["نعم"]] },
        {"range": f"Feuille 1!{chr(64+date_col)}{idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
    ]
    if student2 is not None:
        data.append({"range": f"Feuille 1!{chr(64+student2_col)}{idx}", "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data}
    ).execute()

    # تحديث شيت الطلاب برقم المذكرة
    result_students = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
    values_students = result_students.get('values', [])
    df_students = pd.DataFrame(values_students[1:], columns=values_students[0])
    col_note = df_students.columns.tolist().index("رقم المذكرة") + 1

    # الطالب الأول
    row_idx1 = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
    sheets_service.spreadsheets().values().update(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=f"Feuille 1!{chr(64+col_note)}{row_idx1}",
        valueInputOption="USER_ENTERED",
        body={"values": [[note_number]]}
    ).execute()

    # الطالب الثاني
    if student2 is not None:
        row_idx2 = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{chr(64+col_note)}{row_idx2}",
            valueInputOption="USER_ENTERED",
            body={"values": [[note_number]]}
        ).execute()

    return True

# --- تحميل البيانات ---
df_students = load_students()
df_memos = load_memos()

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.memo_type = "فردية"

# --- واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:white;'>🎓 تسجيل الدخول</h2>", unsafe_allow_html=True)

    st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])
    username1 = st.text_input("اسم المستخدم الطالب 1")
    password1 = st.text_input("كلمة السر الطالب 1", type="password")
    if st.session_state.memo_type == "ثنائية":
        username2 = st.text_input("اسم المستخدم الطالب 2")
        password2 = st.text_input("كلمة السر الطالب 2", type="password")

    if st.button("تسجيل الدخول"):
        valid1, student1 = verify_student(username1, password1, df_students)
        if not valid1:
            st.error(student1)
        elif check_student_already_registered(student1):
            st.error("❌ الطالب 1 سجل مذكرة من قبل!")
        else:
            student2 = None
            if st.session_state.memo_type == "ثنائية":
                valid2, student2 = verify_student(username2, password2, df_students)
                if not valid2:
                    st.error(student2)
                elif check_student_already_registered(student2):
                    st.error("❌ الطالب 2 سجل مذكرة من قبل!")
                else:
                    st.success(f"✅ تم تسجيل الدخول للطالبين: {student1['الإسم']} و {student2['الإسم']}")
            else:
                st.success(f"✅ تم تسجيل الدخول للطالب: {student1['الإسم']}")
            st.session_state.logged_in = True
            st.session_state.student1 = student1
            st.session_state.student2 = student2
    st.markdown('</div>', unsafe_allow_html=True)

# --- صفحة تسجيل المذكرة بعد الدخول ---
else:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;color:white;'>📝 تسجيل المذكرة</h2>", unsafe_allow_html=True)

    # عرض أسماء الطلاب بخط أكبر
    st.markdown(f"<h3 style='color:#FFD700;'>👤 الطالب الأول: {st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}</h3>", unsafe_allow_html=True)
    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
        st.markdown(f"<h3 style='color:#FFD700;'>👤 الطالب الثاني: {st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}</h3>", unsafe_allow_html=True)

    # ملاحظة باللون الأصفر
    st.markdown("<p style='text-align:center; color:#FFFF00; font-size:18px; font-weight:bold;'>⚠️ يجب الاتصال بالأستاذ المشرف للحصول على كلمة السر</p>", unsafe_allow_html=True)

    # إدخال رقم المذكرة وكلمة السر
    note_number = st.text_input("رقم المذكرة")
    memo_password = st.text_input("كلمة سر المذكرة", type="password")

    if st.button("تأكيد تسجيل المذكرة"):
        valid_memo, memo_info, error_msg = verify_memo(note_number, memo_password, df_memos)
        if not valid_memo:
            st.error(error_msg)
        else:
            st.info(f"📄 عنوان المذكرة: {memo_info['عنوان المذكرة']}")
            st.info(f"👨‍🏫 المشرف: {memo_info['الأستاذ']}")
            updated = update_memo_registration(note_number, st.session_state.student1, st.session_state.student2)
            if updated:
                st.success("✅ تم تسجيل المذكرة بنجاح! تم تحديث الشيت.")
    st.markdown('</div>', unsafe_allow_html=True)



