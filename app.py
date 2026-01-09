import streamlit as st
from datetime import datetime
import os
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from PIL import Image

# ------------------- إعداد الصفحة -------------------
st.set_page_config(page_title="منصة تسجيل وإيداع مذكرات التخرج", page_icon="📚", layout="centered")

# ------------------- الاتصال بـ Google Sheets و Drive -------------------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
info = st.secrets["service_account"]
credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

# ------------------- ID للشيتات -------------------
STUDENTS_SPREADSHEET_ID = "1gvNkOVVKo6AO07dRKMnSQw6vZ3KdUnW7I4HBk61Sqns"  # شيت الطلاب
MEMO_SPREADSHEET_ID = "1Ycx-bUscF7rEpse4B5lC4xCszYLZ8uJyPJLp6bFK8zo"   # شيت المذكرات
DRIVE_FOLDER_ID = "1TfhvUA9oqvSlj9TuLjkyHi5xsC5svY1D"

# ------------------- تحميل بيانات الطلاب -------------------
@st.cache_data(ttl=300)
def load_students():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=STUDENTS_SPREADSHEET_ID,
            range="Sheet1!A1:Z1000"
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات في شيت الطلاب.")
            st.stop()
        df_students = pd.DataFrame(values[1:], columns=values[0])
        return df_students
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات الطلاب: {e}")
        st.stop()

# ------------------- تحميل بيانات المذكرات -------------------
@st.cache_data(ttl=300)
def load_memos():
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMO_SPREADSHEET_ID,
            range="Feuille 1!A1:Z1000"
        ).execute()
        values = result.get('values', [])
        if not values:
            st.error("❌ لا توجد بيانات في شيت المذكرات.")
            st.stop()
        df_memos = pd.DataFrame(values[1:], columns=values[0])
        return df_memos
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات المذكرات: {e}")
        st.stop()

# ------------------- دوال مساعدة -------------------
def verify_students_login(df_students, usernames, passwords):
    """
    usernames: قائمة أسماء المستخدمين
    passwords: قائمة كلمات السر
    """
    if len(usernames) != len(passwords):
        return False, None
    memo_number = None
    for user, pwd in zip(usernames, passwords):
        match = df_students[(df_students["اسم المستخدم"] == user) & (df_students["كلمة السر"] == pwd)]
        if match.empty:
            return False, None
        if memo_number is None:
            memo_number = match.iloc[0]["رقم المذكرة"]
        elif memo_number != match.iloc[0]["رقم المذكرة"]:
            return False, None
    return True, memo_number

def is_already_submitted(memo_number, df_memos):
    memo = df_memos[df_memos["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()]
    if memo.empty:
        return False, None
    deposit_status = memo.iloc[0]["تم الإيداع"]
    submission_date = memo.iloc[0]["تاريخ الإيداع"]
    if (isinstance(deposit_status, str) and deposit_status.strip() == "نعم") or \
       (isinstance(submission_date, str) and submission_date.strip() != ""):
        return True, submission_date
    return False, None

def update_submission_status(memo_number):
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=MEMO_SPREADSHEET_ID,
            range="Feuille 1!A1:Z1000"
        ).execute()
        values = result.get('values', [])
        df = pd.DataFrame(values[1:], columns=values[0])

        row_idx = df[df["رقم المذكرة"].astype(str).str.strip() == str(memo_number).strip()].index
        if row_idx.empty:
            st.error("❌ رقم المذكرة غير موجود في الشيت أثناء التحديث.")
            return False

        idx = row_idx[0] + 2
        col_names = df.columns.tolist()
        deposit_col = col_names.index("تم الإيداع") + 1
        date_col = col_names.index("تاريخ الإيداع") + 1

        updates = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"Feuille 1!{chr(64+deposit_col)}{idx}", "values": [["نعم"]]},
                {"range": f"Feuille 1!{chr(64+date_col)}{idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M')]]},
            ]
        }
        sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=MEMO_SPREADSHEET_ID,
            body=updates
        ).execute()
        return True
    except Exception as e:
        st.error(f"❌ فشل تحديث حالة الإيداع: {e}")
        return False

def upload_to_drive(filepath, memo_number):
    try:
        new_name = f"memoire_{memo_number}.pdf"
        media = MediaFileUpload(filepath, mimetype='application/pdf', resumable=True)
        file_metadata = {'name': new_name, 'parents': [DRIVE_FOLDER_ID]}
        uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return uploaded.get('id')
    except Exception as e:
        st.error(f"❌ خطأ في رفع الملف إلى Google Drive: {e}")
        return None

# ------------------- واجهة المستخدم -------------------
st.title("📥 منصة تسجيل وإيداع مذكرات التخرج")

df_students = load_students()
df_memos = load_memos()

# اختيار نوع المذكرة
memo_type = st.radio("اختر نوع المذكرة:", ["فردية", "ثنائية"])

# إدخال معلومات الطلاب
if memo_type == "فردية":
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة السر", type="password")
    usernames = [username]
    passwords = [password]
else:
    col1, col2 = st.columns(2)
    with col1:
        username1 = st.text_input("اسم المستخدم - الطالب الأول")
        password1 = st.text_input("كلمة السر - الطالب الأول", type="password")
    with col2:
        username2 = st.text_input("اسم المستخدم - الطالب الثاني")
        password2 = st.text_input("كلمة السر - الطالب الثاني", type="password")
    usernames = [username1, username2]
    passwords = [password1, password2]

# زر تسجيل الدخول
if st.button("✅ تسجيل الدخول"):
    valid, memo_number = verify_students_login(df_students, usernames, passwords)
    if not valid:
        st.error("❌ اسم المستخدم أو كلمة السر غير صحيحة، أو الطلاب لم يشاركوا نفس رقم المذكرة.")
    else:
        st.success(f"✅ تسجيل الدخول ناجح! رقم المذكرة: {memo_number}")
        # تحقق إذا تم إيداع المذكرة مسبقًا
        already_submitted, submission_date = is_already_submitted(memo_number, df_memos)
        if already_submitted:
            st.warning(f"❌ المذكرة رقم {memo_number} تم إيداعها مسبقًا بتاريخ: {submission_date}")
        else:
            st.markdown("### ⬇️ رفع ملف المذكرة (PDF فقط)")
            uploaded_file = st.file_uploader("اختر الملف", type="pdf")
            if uploaded_file:
                temp_filename = f"temp_memo_{memo_number}.pdf"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with st.spinner("⏳ جاري رفع الملف..."):
                    file_id = upload_to_drive(temp_filename, memo_number)
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                if file_id:
                    updated = update_submission_status(memo_number)
                    if updated:
                        st.success("✅ تم إيداع المذكرة وتحديث الحالة بنجاح!")
                        st.markdown(f"📎 معرف الملف على Drive: {file_id}")
                        st.download_button(
                            label="📄 تحميل وصل الإيداع",
                            data=f"وصل تأكيد إيداع\nرقم المذكرة: {memo_number}\nتاريخ الإيداع: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                            file_name="وصل_الإيداع.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("❌ فشل تحديث حالة الإيداع.")
                else:
                    st.error("❌ فشل رفع الملف إلى Drive.")
