import streamlit as st
from datetime import datetime
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# إعداد الصفحة
st.set_page_config(page_title="تسجيل مذكرة الماستر", layout="centered")

# --- تصميم خلفية زرقاء ليلية ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"]  {
    font-family: 'Cairo', sans-serif !important;
}
.main {
    background-color: #1E2A38;
    color: #ffffff;
}
.block-container {
    padding: 2rem;
    background-color: #243447;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    max-width: 700px;
    margin: auto;
}
label, h1, h2, h3, h4, h5, h6, p, span {
    color: #ffffff !important;
}
input, button {
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

# --- إعداد الاتصال بـ Google Sheets ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=credentials)

STUDENTS_SHEET_ID = "ضع هنا ID شيت الطلاب"
MEMOS_SHEET_ID = "ضع هنا ID شيت المذكرات"

@st.cache_data(ttl=300)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SHEET_ID,
            range="Feuille 1!A1:Z1000"
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات الطلاب في الشيت.")
            st.stop()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات الطلاب: {e}")
        st.stop()

@st.cache_data(ttl=300)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMOS_SHEET_ID,
            range="Feuille 1!A1:Z1000"
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات المذكرات في الشيت.")
            st.stop()
        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات المذكرات: {e}")
        st.stop()

df_students = load_students()
df_memos = load_memos()

# --- عنوان الجامعة والكلية ---
st.markdown("<div style='text-align: center; color: white; font-weight: bold; font-size: 18px;'>جامعة محمد البشير الإبراهيمي - برج بوعريريج</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: white; font-weight: bold; font-size: 18px;'>كلية الحقوق والعلوم السياسية</div>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;color:white;'>🎓 منصة تسجيل مذكرة الماستر</h2>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:white;'>---</div>", unsafe_allow_html=True)

# --- اختيار نوع المذكرة ---
memo_type = st.radio("اختر نوع المذكرة:", ("فردية", "ثنائية"))

# --- إدخال بيانات الطالب/الطلاب ---
with st.form("student_form"):
    note_number = st.text_input("🔢 أدخل رقم المذكرة:")
    
    username1 = st.text_input("اسم المستخدم للطالب 1:")
    password1 = st.text_input("كلمة السر للطالب 1:", type="password")
    
    if memo_type == "ثنائية":
        username2 = st.text_input("اسم المستخدم للطالب 2:")
        password2 = st.text_input("كلمة السر للطالب 2:", type="password")
    
    memo_password = st.text_input("🔐 كلمة السر الخاصة بالمذكرة:", type="password")
    
    submitted = st.form_submit_button("✅ تسجيل المذكرة")

if submitted:
    # التحقق من المذكرة مسجلة مسبقًا
    memo_row = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(note_number).strip()]
    if memo_row.empty:
        st.error("❌ رقم المذكرة غير موجود.")
    elif str(memo_row.iloc[0]["تم التسجيل"]).strip() == "نعم":
        st.error(f"❌ المذكرة رقم {note_number} تم تسجيلها مسبقًا.")
    else:
        # التحقق من الطلاب
        student1_row = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username1.strip()]
        if student1_row.empty:
            st.error("❌ الطالب 1 غير موجود.")
        elif student1_row.iloc[0]["كلمة السر"].strip() != password1.strip():
            st.error("❌ كلمة سر الطالب 1 غير صحيحة.")
        elif str(student1_row.iloc[0]["رقم المذكرة"]).strip() != note_number.strip():
            st.error("❌ الطالب 1 لا يملك هذه المذكرة.")
        else:
            if memo_type == "ثنائية":
                student2_row = df_students[df_students["اسم المستخدم"].astype(str).str.strip() == username2.strip()]
                if student2_row.empty:
                    st.error("❌ الطالب 2 غير موجود.")
                elif student2_row.iloc[0]["كلمة السر"].strip() != password2.strip():
                    st.error("❌ كلمة سر الطالب 2 غير صحيحة.")
                elif str(student2_row.iloc[0]["رقم المذكرة"]).strip() != note_number.strip():
                    st.error("❌ الطالب 2 لا يملك هذه المذكرة.")
                else:
                    # عرض معلومات المذكرة
                    st.info(f"📄 عنوان المذكرة: {memo_row.iloc[0]['عنوان المذكرة']}")
                    st.info(f"👨‍🏫 المشرف: {memo_row.iloc[0]['الأستاذ']}")
                    # تحديث الشيت
                    update_body = {
                        "valueInputOption": "USER_ENTERED",
                        "data": [
                            {"range": f"Feuille 1!J{memo_row.index[0]+2}", "values": [["نعم"]]},
                            {"range": f"Feuille 1!K{memo_row.index[0]+2}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
                        ]
                    }
                    sheets_service.spreadsheets().values().batchUpdate(
                        spreadsheetId=MEMOS_SHEET_ID,
                        body=update_body
                    ).execute()
                    st.success("✅ تم تسجيل المذكرة بنجاح.")
            else:
                # فردية
                st.info(f"📄 عنوان المذكرة: {memo_row.iloc[0]['عنوان المذكرة']}")
                st.info(f"👨‍🏫 المشرف: {memo_row.iloc[0]['الأستاذ']}")
                # تحديث الشيت
                update_body = {
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": f"Feuille 1!J{memo_row.index[0]+2}", "values": [["نعم"]]},
                        {"range": f"Feuille 1!K{memo_row.index[0]+2}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]}
                    ]
                }
                sheets_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=MEMOS_SHEET_ID,
                    body=update_body
                ).execute()
                st.success("✅ تم تسجيل المذكرة بنجاح.")
