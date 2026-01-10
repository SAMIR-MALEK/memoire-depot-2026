import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------
# إعداد صفحة Streamlit
# ---------------------------
st.set_page_config(
    page_title="تسجيل مذكرة الماستر",
    page_icon="🎓",
    layout="centered"
)

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
credentials = Credentials.from_service_account_info(
    st.secrets["service_account"],  # معلومات حساب الخدمة
    scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)

# معرفات الشيتات
STUDENTS_SHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"          # شيت الطلبة
MEMOS_SHEET_ID = "1LNJMBAye4QIQy7JHz6F8mQ6-XNC1weZx1ozDZFfjD5s"            # شيت حالة تسجيل المذكرات
SUPERVISOR_SHEET_ID = "1OnZi1o-oPMUI_W_Ew-op0a1uOhSj006hw_2jrMD6FSE"      # شيت المذكرات - الأساتذة

STUDENTS_RANGE = "Feuille 1!A1:K1000"
MEMOS_RANGE = "Feuille 1!A1:N1000"
SUPERVISOR_RANGE = "Feuille 1!A1:K1000"

# ---------------------------
# تحميل البيانات
# ---------------------------
@st.cache_data(ttl=300)
def load_students():
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

@st.cache_data(ttl=300)
def load_memos():
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

@st.cache_data(ttl=300)
def load_supervisor():
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SUPERVISOR_SHEET_ID,
        range=SUPERVISOR_RANGE
    ).execute()
    values = result.get('values', [])
    if not values:
        st.error("❌ لا توجد بيانات في شيت المذكرات - الأساتذة.")
        st.stop()
    df = pd.DataFrame(values[1:], columns=values[0])
    return df

# ---------------------------
# التحقق من بيانات الطالب
# ---------------------------
def verify_student(username, password, df):
    row = df[df["اسم المستخدم"].astype(str).str.strip() == username.strip()]
    if row.empty:
        return False, "❌ اسم المستخدم غير موجود."
    if row.iloc[0]["كلمة السر"].strip() != password.strip():
        return False, "❌ كلمة السر غير صحيحة."
    return True, row.iloc[0]

def student_has_memo(student):
    return str(student["رقم المذكرة"]).strip() != ""

# ---------------------------
# التحقق من المذكرة
# ---------------------------
def verify_memo(note_number, memo_password, df_memos, df_supervisor):
    # البحث في شيت حالة تسجيل المذكرات
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if not memo_row.empty:
        # إذا كان هناك بيانات مسبقة => محجوزة
        row = memo_row.iloc[0]
        if str(row.get("تم التسجيل", "")).strip() == "نعم" or row["الطالب الأول"].strip() != "":
            return False, None, "❌ هذه المذكرة محجوزة مسبقًا!"
    
    # البحث في شيت المذكرات - الأساتذة لتأكيد كلمة السر
    # أولًا نأخذ اسم الأستاذ من شيت الحالة (إذا وجد) أو نفترض أنه مدخل من قبل المستخدم
    supervisor_row = df_supervisor[df_supervisor["كلمة سر التسجيل"].astype(str).str.strip() == memo_password.strip()]
    if supervisor_row.empty:
        return False, None, "❌ كلمة سر المشرف غير صحيحة أو مستعملة مسبقًا."
    
    # إذا كل شيء صحيح نرجع البيانات
    return True, supervisor_row.iloc[0], None

# ---------------------------
# تحديث التسجيل
# ---------------------------
def update_registration(note_number, student1, student2=None):
    df_memos = load_memos()
    df_supervisor = load_supervisor()
    
    # تحديد الصف في شيت حالة تسجيل المذكرات
    idx_memo = df_memos.index[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if idx_memo.empty:
        # إذا الرقم غير موجود، نضيفه في أول صف فارغ
        idx = len(df_memos) + 2
    else:
        idx = idx_memo[0] + 2

    cols = df_memos.columns.tolist()
    updates = []

    updates.append({
        "range": f"Feuille 1!{chr(65+cols.index('الطالب الأول'))}{idx}",
        "values": [[student1["اللقب"] + " " + student1["الإسم"]]]
    })
    if student2 is not None:
        updates.append({
            "range": f"Feuille 1!{chr(65+cols.index('الطالب الثاني'))}{idx}",
            "values": [[student2["اللقب"] + " " + student2["الإسم"]]]
        })

    updates += [
        {"range": f"Feuille 1!{chr(65+cols.index('رقم المذكرة'))}{idx}", "values": [[note_number]]},
        {"range": f"Feuille 1!{chr(65+cols.index('تم التسجيل'))}{idx}", "values": [["نعم"]]},
        {"range": f"Feuille 1!{chr(65+cols.index('تاريخ التسجيل'))}{idx}", "values": [[datetime.now().strftime("%Y-%m-%d %H:%M")]]}
    ]

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=MEMOS_SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": updates}
    ).execute()

    # تحديث شيت الطلبة برقم المذكرة
    df_students = load_students()
    col_note = df_students.columns.tolist().index("رقم المذكرة") + 1
    for stt in [student1, student2]:
        if stt is not None:
            row_idx = df_students.index[df_students["اسم المستخدم"].astype(str).str.strip() == stt["اسم المستخدم"].strip()][0] + 2
            sheets_service.spreadsheets().values().update(
                spreadsheetId=STUDENTS_SHEET_ID,
                range=f"Feuille 1!{chr(64+col_note)}{row_idx}",
                valueInputOption="USER_ENTERED",
                body={"values": [[note_number]]}
            ).execute()

# ---------------------------
# واجهة المستخدم
# ---------------------------
df_students = load_students()
df_memos = load_memos()
df_supervisor = load_supervisor()

if "logged" not in st.session_state:
    st.session_state.logged = False

# صفحة تسجيل الدخول
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
        if not ok1:
            st.error(s1)
            st.stop()
        if student_has_memo(s1):
            st.error("❌ الطالب الأول سجل مذكرة من قبل!")
            st.stop()

        s2 = None
        if memo_type == "ثنائية":
            ok2, s2 = verify_student(u2, p2, df_students)
            if not ok2:
                st.error(s2)
                st.stop()
            if student_has_memo(s2):
                st.error("❌ الطالب الثاني سجل مذكرة من قبل!")
                st.stop()

        st.session_state.logged = True
        st.session_state.s1 = s1
        st.session_state.s2 = s2
        st.session_state.memo_type = memo_type

        st.success(f"✅ تسجيل الدخول ناجح\n👤 الطالب الأول: {s1['اللقب']} {s1['الإسم']}")
        if s2:
            st.success(f"👤 الطالب الثاني: {s2['اللقب']} {s2['الإسم']}")

# صفحة تسجيل المذكرة
else:
    st.markdown("## 📝 تسجيل المذكرة")
    note = st.text_input("رقم المذكرة")
    pwd = st.text_input("كلمة سر المشرف", type="password")

    if st.button("تأكيد التسجيل"):
        ok, memo, err = verify_memo(note, pwd, df_memos, df_supervisor)
        if not ok:
            st.error(err)
            st.stop()

        # تحديث الشيتات بعد التأكد من صحة البيانات
        update_registration(note, st.session_state.s1, st.session_state.s2)

        # عرض ملخص التسجيل بدون PDF
        st.success(
            f"✅ تم تسجيل المذكرة بنجاح!\n"
            f"📄 العنوان: {memo['عنوان المذكرة']}\n"
            f"👨‍🏫 المشرف: {memo['الأستاذ']}\n"
            f"📝 التخصص: {memo.get('التخصص', 'غير محدد')}"
        )