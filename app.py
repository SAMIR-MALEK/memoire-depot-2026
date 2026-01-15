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

STUDENTS_RANGE = "Feuille 1!A1:L1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
PROF_MEMOS_RANGE = "Feuille 1!A1:L1000"

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

# ---------------- التحقق من كلمة سر الأستاذ ----------------
def verify_professor_password(note_number, prof_password, df_memos, df_prof_memos):
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo_row.empty: return False, None, "❌ رقم المذكرة غير موجود."
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

    prof_name = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]["الأستاذ"].iloc[0].strip()
    prof_row_idx = df_prof_memos[
        (df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name) &
        (df_prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
    ].index[0] + 2

    col_names = df_prof_memos.columns.tolist()
    updates = [
        {"range": f"Feuille 1!{chr(64+col_names.index('الطالب الأول')+1)}{prof_row_idx}",
         "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('تم التسجيل')+1)}{prof_row_idx}",
         "values": [["نعم"]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('تاريخ التسجيل')+1)}{prof_row_idx}",
         "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
        {"range": f"Feuille 1!{chr(64+col_names.index('رقم المذكرة')+1)}{prof_row_idx}",
         "values": [[note_number]]}
    ]
    if student2 is not None:
        updates.append({"range": f"Feuille 1!{chr(64+col_names.index('الطالب الثاني')+1)}{prof_row_idx}",
                        "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=PROF_MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

    # تحديث شيت "حالة تسجيل المذكرات"
    memo_row_idx = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()].index[0] + 2
    memo_cols = df_memos.columns.tolist()
    updates2 = [
        {"range": f"Feuille 1!{chr(64+memo_cols.index('الطالب الأول')+1)}{memo_row_idx}",
         "values": [[student1['اللقب'] + ' ' + student1['الإسم']]]},
        {"range": f"Feuille 1!{chr(64+memo_cols.index('تم التسجيل')+1)}{memo_row_idx}",
         "values": [["نعم"]]},
        {"range": f"Feuille 1!{chr(64+memo_cols.index('تاريخ التسجيل')+1)}{memo_row_idx}",
         "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
    ]
    if student2 is not None:
        updates2.append({"range": f"Feuille 1!{chr(64+memo_cols.index('الطالب الثاني')+1)}{memo_row_idx}",
                         "values": [[student2['اللقب'] + ' ' + student2['الإسم']]]})

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

    if student2 is not None:
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
    st.session_state.mode = "register"

# ---------------- واجهة تسجيل الدخول ----------------
# ... (هنا تضيف الكود من الجزء الثالث كما أرسلته أعلاه)
# ---------------- واجهة تسجيل الدخول ----------------
if not st.session_state.logged_in:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("<h5 style='text-align:center;'>جامعة محمد البشير الإبراهيمي</h5>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align:center;'>كلية الحقوق والعلوم السياسية</h6>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align:center; margin:20px 0;">
            <img src="https://raw.githubusercontent.com/SAMIR-MALEK/memoire-depot-2026/main/LOGO2.png" width="100">
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center; color:#FFD700;'>منصة تسجيل مذكرة الماستر</h4>", unsafe_allow_html=True)

    st.session_state.memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])
    username1 = st.text_input("اسم المستخدم الطالب الأول")
    password1 = st.text_input("كلمة السر الطالب الأول", type="password")
    username2 = password2 = None
if st.session_state.memo_type == "ثنائية":
    username2 = st.text_input("اسم المستخدم الطالب الثاني")
    password2 = st.text_input("كلمة السر الطالب الثاني", type="password")

if st.button("تسجيل الدخول"):
    
    # التحقق من الطالب الأول
    valid1, student1 = verify_student(username1, password1, df_students)
    
    
    if not valid1:
        st.markdown(f'<p class="message">❌ {student1}</p>', unsafe_allow_html=True)
    else:
        # ===== تحقق من عمود "فردية" إذا كانت المذكرة فردية =====
        if st.session_state.memo_type == "فردية":
            value = str(student1.get("فردية", "")).strip().lower()  # قراءة العمود وتحويله للصغير
            
            if value not in ["1", "نعم"]:  # قبول "1" أو "نعم"
                st.markdown(
                    '<div class="block-container">'
                    '<h4 style="text-align:center; color:#FF4500;">❌ لا يمكن تسجيل مذكرة فردية. يرجى الاتصال بمسؤول الميدان للحصول على الموافقة</h4>'
                    '<p style="text-align:center; color:#FFD700;">📧 Email: domaie.dsp@univ-bba.dz</p>'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.stop()
        
        # متابعة باقي تسجيل الدخول
        student2 = None
        n1 = str(student1.get('رقم المذكرة', '')).strip()
        if st.session_state.memo_type == "ثنائية":
            valid2, student2 = verify_student(username2, password2, df_students)
            if not valid2:
                st.markdown(f'<p class="message">❌ {student2}</p>', unsafe_allow_html=True)
                st.stop()
            n2 = str(student2.get('رقم المذكرة', '')).strip()
            if n1 and n2 and n1 != n2:
                st.markdown('<p class="message">❌ أحد الطالبين مسجل مسبقًا أو مسجل في مذكرتين مختلفتين!</p>', unsafe_allow_html=True)
                st.stop()
            st.session_state.mode = "register" if not n1 else "view"
        else:
            st.session_state.mode = "register" if not n1 else "view"

        st.session_state.logged_in = True
        st.session_state.student1 = student1
        st.session_state.student2 = student2




    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- فضاء الطالب (عرض فقط) محدث ----------------
if st.session_state.logged_in and st.session_state.mode == "view":
    s1 = st.session_state.student1
    note_number = str(s1.get("رقم المذكرة", "")).strip()

    # التحقق من وجود رقم المذكرة في جدول المذكرات
    memo_info = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == note_number]
    if memo_info.empty:
        st.error("❌ لم يتم العثور على المذكرة المسجلة لهذا الطالب")
        st.stop()
    memo_info = memo_info.iloc[0]

    # جلب بيانات المشرف الفعلية من جدول الأساتذة
    prof_info = df_prof_memos[
        (df_prof_memos["الطالب الأول"].astype(str).str.strip() == f"{s1['اللقب']} {s1['الإسم']}")
    ]
    
    # إذا كانت المذكرة ثنائية، تحقق من الطالب الثاني
    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
        s2 = st.session_state.student2
        prof_info2 = df_prof_memos[
            (df_prof_memos["الطالب الثاني"].astype(str).str.strip() == f"{s2['اللقب']} {s2['الإسم']}")
        ]
        if not prof_info2.empty:
            prof_info = prof_info2

    # تحديد المشرف الفعلي
    if prof_info.empty:
        actual_prof = memo_info['الأستاذ']  # fallback
    else:
        actual_prof = prof_info.iloc[0]["الأستاذ"]
    actual_prof = memo_info["الأستاذ"]


    # بناء واجهة العرض
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>📘 فضاء الطالب</h2>", unsafe_allow_html=True)

    st.info("الطالب / الطالبين مسجلين سابقا")

    # بيانات الطلاب
    st.markdown(f"👤 الطالب الأول: {s1['اللقب']} {s1['الإسم']}", unsafe_allow_html=True)
    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
        st.markdown(f"👤 الطالب الثاني: {s2['اللقب']} {s2['الإسم']}", unsafe_allow_html=True)

    # بيانات المذكرة
    st.markdown(f"📄 رقم المذكرة: {memo_info['رقم المذكرة']}", unsafe_allow_html=True)
    st.markdown(f"📑 عنوان المذكرة: {memo_info['عنوان المذكرة']}", unsafe_allow_html=True)
    st.markdown(f"🎯 التخصص: {memo_info['التخصص']}", unsafe_allow_html=True)
#   st.markdown(f"👨‍🏫 المشرف: {actual_prof}", unsafe_allow_html=True)
    st.markdown(f"🕒 تاريخ التسجيل: {memo_info.get('تاريخ التسجيل', '')}", unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- تسجيل المذكرة جديد ----------------
if st.session_state.logged_in and st.session_state.mode == "register":
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>📝 تسجيل المذكرة</h2>", unsafe_allow_html=True)
    st.markdown(f"👤 الطالب الأول: {st.session_state.student1['اللقب']} {st.session_state.student1['الإسم']}", unsafe_allow_html=True)
    if st.session_state.memo_type == "ثنائية" and st.session_state.student2 is not None:
        st.markdown(f"👤 الطالب الثاني: {st.session_state.student2['اللقب']} {st.session_state.student2['الإسم']}", unsafe_allow_html=True)

    st.markdown('<p class="message">⚠️ اختر الأستاذ لمعرفة المذكرات المتاحة (للاطلاع فقط)</p>', unsafe_allow_html=True)

    # -------- قائمة الأساتذة --------
    all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
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

    note_number = st.text_input("رقم المذكرة")
    prof_password = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد تسجيل المذكرة"):
        valid_memo, prof_row, error_msg = verify_professor_password(note_number, prof_password, df_memos, df_prof_memos)
        if not valid_memo:
            st.markdown(f'<p class="message">❌ {error_msg}</p>', unsafe_allow_html=True)
        else:
            if st.session_state.memo_type == "فردية":
                update_registration(note_number, st.session_state.student1)
                st.markdown(f'<p class="message">✅ تم تسجيل المذكرة بنجاح!</p>', unsafe_allow_html=True)
                st.session_state.mode = "view"
            else:
                student2 = st.session_state.student2
                update_registration(note_number, st.session_state.student1, student2)
                st.markdown(f'<p class="message">✅ تم تسجيل المذكرة الثنائية بنجاح!</p>', unsafe_allow_html=True)
                st.session_state.mode = "view"

    st.markdown('</div>', unsafe_allow_html=True)
