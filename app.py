import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------- إعداد الصفحة ----------------
st.set_page_config(page_title="تسجيل مذكرة ماستر", page_icon="🎓", layout="centered")

# ---------------- CSS للواجهة ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Cairo', sans-serif !important; }
.main { background-color: #0A1B2C; color: #ffffff; }
.block-container { padding: 2rem; background-color: #1A2A3D; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); max-width: 750px; margin: auto; }
label, h1, h2, h3, h4, h5, h6, p, span, .stTextInput label { color: #ffffff !important; }
input, button, select { font-size: 16px !important; }
button { background-color: #256D85 !important; color: white !important; border: none !important; padding: 10px 20px !important; border-radius: 6px !important; transition: background-color 0.3s ease; }
button:hover { background-color: #2C89A0 !important; }
hr { border: 1px solid #00CED1; margin: 20px 0; }
.message { font-size: 18px; font-weight: bold; text-align: center; margin: 10px 0; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ---------------- اتصال Google Sheets ----------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

# ---------------- معرفات الشيتات ----------------
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"
PROF_MEMOS_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:K1000"

# ---------------- تحميل البيانات ----------------
@st.cache_data(ttl=300)
def load_students():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=STUDENTS_SHEET_ID, range=STUDENTS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة الطلاب."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_memos():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=MEMOS_SHEET_ID, range=MEMOS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة المذكرات."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

@st.cache_data(ttl=300)
def load_prof_memos():
    result = sheets_service.spreadsheets().values().get(spreadsheetId=PROF_MEMOS_SHEET_ID, range=PROF_MEMOS_RANGE).execute()
    values = result.get('values', [])
    if not values: st.error("❌ لا توجد بيانات في صفحة المذكرات - الأساتذة."); st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# ---------------- التحقق من الطالب ----------------
def verify_student(username, password, df_students):
    student = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if student.empty: return False, "❌ اسم المستخدم غير موجود."
    if student.iloc[0]["كلمة السر"].strip() != password.strip(): return False, "❌ كلمة السر غير صحيحة."
    return True, student.iloc[0]

def check_student_already_registered(student):
    return str(student['رقم المذكرة']).strip() != ""

# ---------------- التحقق من كلمة سر الأستاذ ----------------
def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo_row.empty:
        return False, None, "❌ رقم المذكرة غير موجود."
    memo_row = memo_row.iloc[0]

    prof_row = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == memo_row["الأستاذ"].strip()) &
        (df_prof_memos["كلمة سر التسجيل"].astype(str).str.strip() == prof_password.strip())
    ]
    if prof_row.empty:
        return False, None, "❌ كلمة سر المشرف غير صحيحة أو غير مخصصة لهذه المذكرة."
    if str(prof_row.iloc[0].get("تم التسجيل", "")).strip() == "نعم":
        return False, None, "❌ هذه كلمة السر تم استعمالها مسبقًا."

    return True, prof_row.iloc[0], None

# ---------------- تحديث الشيتات ----------------
def update_registration(note_number, student1, student2=None):
    df_memos = load_memos()
    df_prof_memos = load_prof_memos()
    df_students = load_students()

    # تحديث شيت "المذكرات - الأساتذة"
    prof_row_idx = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]["الأستاذ"].strip()) &
        (df_prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
    ].index[0] + 2
    col_names = df_prof_memos.columns.tolist()
    updates = [
        {"range": f"Feuille 1!{chr(64+col_names.index('الطالب الأول')+1)}{prof_row_idx}", "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('تم التسجيل')+1)}{prof_row_idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('رقم المذكرة')+1)}{prof_row_idx}", "values": [[note_number]]}
    ]
    if student2:
        updates.append({"range": f"Feuille 1!{chr(64+col_names.index('الطالب الثاني')+1)}{prof_row_idx}", "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=PROF_MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

    # تحديث شيت "حالة تسجيل المذكرات"
    memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
    memo_cols = df_memos.columns.tolist()
    updates2 = [
        {"range": f"Feuille 1!{chr(64+memo_cols.index('الطالب الأول')+1)}{memo_row_idx}", "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
        {"range": f"Feuille 1!{chr(64+memo_cols.index('تم التسجيل')+1)}{memo_row_idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{chr(64+memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
    ]
    if student2:
        updates2.append({"range": f"Feuille 1!{chr(64+memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}", "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates2}
    ).execute()

    # تحديث شيت "الطلبة"
    students_cols = df_students.columns.tolist()
    student1_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student1['اسم المستخدم'].strip()].index[0] + 2
    sheets_service.spreadsheets().values().update(
        spreadsheetId=STUDENTS_SHEET_ID,
        range=f"Feuille 1!{chr(64+students_cols.index('رقم المذكرة')+1)}{student1_row_idx}",
        valueInputOption="USER_ENTERED",
        body={"values": [[note_number]]}
    ).execute()
    if student2:
        student2_row_idx = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == student2['اسم المستخدم'].strip()].index[0] + 2
        sheets_service.spreadsheets().values().update(
            spreadsheetId=STUDENTS_SHEET_ID,
            range=f"Feuille 1!{chr(64+students_cols.index('رقم المذكرة')+1)}{student2_row_idx}",
            valueInputOption="USER_ENTERED",
            body={"values": [[note_number]]}
        ).execute()

    return True

# ---------------- تحميل البيانات ----------------
df_students = load_students()
df_memos = load_memos()
df_prof_memos = load_prof_memos()

# ---------------- Session State ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student1 = None
    st.session_state.student2 = None
    st.session_state.memo_type = "فردية"

# ---------------- واجهة تسجيل الدخول ----------------
if not st.session_state.logged_in:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)

    # 1. عنوان الجامعة
    st.markdown("<h5 style='text-align:center;'>جامعة محمد البشير الإبراهيمي</h2>", unsafe_allow_html=True)
    # 2. عنوان الكلية
    st.markdown("<h6 style='text-align:center;'>كلية الحقوق والعلوم السياسية</h3>", unsafe_allow_html=True)

    # 3. اللوجو في الوسط
    st.markdown("""
        <div style="text-align:center; margin:20px 0;">
            <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="100">
        </div>
    """, unsafe_allow_html=True)

    # 4. عنوان المنصة بالأصفر
    st.markdown("<h4 style='text-align:center; color:#FFD700;'>منصة تسجيل مذكرة الماستر</h2>", unsafe_allow_html=True)

    # --- اختيار نوع المذكرة ---
    st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])
    username1 = st.text_input("اسم المستخدم الطالب الأول")
    password1 = st.text_input("كلمة السر الطالب الأول", type="password")
    if st.session_state.memo_type == "ثنائية":
        username2 = st.text_input("اسم المستخدم الطالب الثاني")
        password2 = st.text_input("كلمة السر الطالب الثاني", type="password")

    if st.button("تسجيل الدخول"):
        valid1, student1 = verify_student(username1, password1, df_students)
        if not valid1:
            st.markdown(f'<p class="message">❌ {student1}</p>', unsafe_allow_html=True)
        elif check_student_already_registered(student1):
            st.markdown('<p class="message">❌ الطالب الأول سجل مذكرة من قبل!</p>', unsafe_allow_html=True)
        else:
            student2 = None
            if st.session_state.memo_type == "ثنائية":
                valid2, student2 = verify_student(username2, password2, df_students)
                if not valid2:
                    st.markdown(f'<p class="message">❌ {student2}</p>', unsafe_allow_html=True)
                elif check_student_already_registered(student2):
                    st.markdown('<p class="message">❌ الطالب الثاني سجل مذكرة من قبل!</p>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<p class="message">✅ تم تسجيل الدخول للطالبين: {student1["اللقب"]} {student1["الإسم"]} و {student2["اللقب"]} {student2["الإسم"]}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="message">✅ تم تسجيل الدخول للطالب: {student1["اللقب"]} {student1["الإسم"]}</p>', unsafe_allow_html=True)
            st.session_state.logged_in = True
            st.session_state.student1 = student1
            st.session_state.student2 = student2

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- صفحة تسجيل المذكرة بعد تسجيل الدخول ----------------
else:
    # ---------- الجزء الذي أرسلته مسبقًا مع قائمة الأساتذة ---------- #
    # ---------------- واجهة تسجيل المذكرة بعد الدخول ----------------
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;'>📝 تسجيل المذكرة</h2>", unsafe_allow_html=True)
st.markdown(f"<h3>👤 الطالب الأول: {st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}</h3>", unsafe_allow_html=True)
if st.session_state.memo_type == "ثنائية" and st.session_state.student2:
    st.markdown(f"<h3>👤 الطالب الثاني: {st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}</h3>", unsafe_allow_html=True)

st.markdown('<p class="message">⚠️ اختر الأستاذ لمعرفة المذكرات المتاحة (للاطلاع فقط)</p>', unsafe_allow_html=True)

# -------- قائمة الأساتذة مرتبة أبجديًا --------
all_profs = sorted(df_memos["الأستاذ"].dropna().unique().tolist())
selected_prof = st.selectbox("اختر الأستاذ:", [""] + all_profs)

if selected_prof:
    student_specialty = st.session_state.student1["التخصص"]
    available_memos_df = df_memos[
        (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
        (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
        (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
    ][["رقم المذكرة", "عنوان المذكرة"]]

    if not available_memos_df.empty:
        st.markdown(f'<p style="color:#FFD700;">⚠️ هذه المذكرات متاحة فقط لتخصصك: {student_specialty}</p>', unsafe_allow_html=True)
        st.markdown("📚 **المذكرات المتاحة:**")
        for idx, row in available_memos_df.iterrows():
            st.markdown(f'<p style="color:white;">{row["رقم المذكرة"]} • {row["عنوان المذكرة"]}</p>', unsafe_allow_html=True)
    else:
        st.markdown("❌ لا توجد مذكرات متاحة لهذا الأستاذ مع تخصصك.", unsafe_allow_html=True)

# -------- إدخال رقم المذكرة وكلمة سر المشرف --------
note_number = st.text_input("رقم المذكرة")
prof_password = st.text_input("كلمة سر المشرف", type="password")

if st.button("تأكيد تسجيل المذكرة"):
    valid_memo, prof_row, error_msg = verify_professor_password(note_number, prof_password, df_memos, df_prof_memos)
    if not valid_memo:
        st.markdown(f'<p class="message">{error_msg}</p>', unsafe_allow_html=True)
    else:
        updated = update_registration(note_number, st.session_state.student1, st.session_state.student2)
        if updated:
            memo_info = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].iloc[0]
            students_info = [f"{st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}"]
            if st.session_state.student2:
                students_info.append(f"{st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}")
            st.markdown(f'<p class="message">✅ تم تسجيل المذكرة بنجاح! تم تحديث البيانات.</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">📄 رقم المذكرة: {note_number}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">📑 عنوان المذكرة: {memo_info["عنوان المذكرة"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">🎯 التخصص: {memo_info["التخصص"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">👨‍🏫 المشرف: {memo_info["الأستاذ"]}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">👤 الطلاب: {", ".join(students_info)}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="message">🕒 تاريخ التسجيل: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)