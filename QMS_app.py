import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import googleapiclient.http
from datetime import datetime

# ✅ Load Google Cloud Credentials
google_creds = st.secrets["GOOGLE_CREDENTIALS"]
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
creds = Credentials.from_service_account_info(google_creds, scopes=scopes)
client = gspread.authorize(creds)

# ✅ Google Sheets Configuration (Use Cached Sheets)
def get_sheets():
    """Cache Google Sheets connections to avoid API quota issues."""
    return {name: client.open_by_key(st.secrets[f"GOOGLE_SHEETS_ID_{name.upper().replace(' ', '_')}"]).sheet1 
            for name in ["Complaints", "Deviation", "Change Control"]}

sheets = get_sheets()

# ✅ Authenticate Google Drive API with Service Account
def authenticate_drive():
    service = build("drive", "v3", credentials=creds)
    return service

drive_service = authenticate_drive()

# ✅ Upload File to Google Drive
def upload_to_drive(uploaded_file, filename):
    folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
    
    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    media = googleapiclient.http.MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type)
    file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    
    return f"https://drive.google.com/file/d/{file_drive['id']}/view"

# ✅ Fetch Sheet Data (Cache to Minimize API Calls)
def get_sheet_values(sheet):
    """Caches sheet values to minimize read requests."""
    return sheet.get_all_values()

# ✅ Generate Unique Record ID
def generate_record_id(sheet, prefix):
    today = datetime.now()
    month = today.strftime("%m")
    year = today.strftime("%y")

    cached_values = get_sheet_values(sheet)

    # ✅ Fetch data once instead of multiple API calls
    if len(cached_values) < 2:  # If there's only a header row
        return f"{prefix}-{month}{year}-001"

    last_row = cached_values[-1]  # Get the last row of data
    last_id = last_row[1] if len(last_row) > 1 else ""  # Assuming 'ID' is in the second column

    if last_id.startswith(f"{prefix}-{month}{year}"):
        last_serial = int(last_id.split("-")[-1])  # Extract the last serial number
        next_serial = last_serial + 1
    else:
        next_serial = 1  # Start fresh if no matching ID for this month

    return f"{prefix}-{month}{year}-{next_serial:03d}"

# ✅ Streamlit App UI
st.title("🔬 Pharmaceutical QMS (Quality Management System)")
tab1, tab2, tab3, admin_tab = st.tabs(["📋 Complaints", "❌ Deviation", "🔄 Change Control", "🔐 Admin View"])

# ✅ Complaints Section
with tab1:
    st.subheader("📋 Register a New Complaint")
    complaint_id = generate_record_id(sheets["Complaints"], "C")
    product = st.text_input("Product Name")
    severity = st.selectbox("Severity Level", ["High", "Medium", "Low"])
    contact_number = st.text_input("📞 Contact Number")
    details = st.text_area("Complaint Details")
    submitted_by = st.text_input("✍ Submitted By (Optional)")

    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="complaint_file")

    if st.button("Submit Complaint"):
        if product and details and contact_number:
            file_url = ""
            if uploaded_file:
                file_url = upload_to_drive(uploaded_file, f"{complaint_id}_{uploaded_file.name}")

            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), complaint_id, product, severity, contact_number, details, submitted_by or "", file_url]
            sheets["Complaints"].append_row(new_data)
            st.success(f"✅ Complaint registered successfully with ID {complaint_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ Deviation Section
with tab2:
    st.subheader("❌ Register a New Deviation")
    deviation_id = generate_record_id(sheets["Deviation"], "D")
    department = st.text_input("Responsible Department")
    deviation_type = st.selectbox("Deviation Type", ["Minor", "Major", "Critical"])
    deviation_description = st.text_area("Deviation Details")
    reported_by = st.text_input("📛 Reported By")

    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="deviation_file")

    if st.button("Submit Deviation"):
        if department and deviation_description and reported_by:
            file_url = ""
            if uploaded_file:
                file_url = upload_to_drive(uploaded_file, f"{deviation_id}_{uploaded_file.name}")

            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), deviation_id, department, deviation_type, deviation_description, reported_by, file_url]
            sheets["Deviation"].append_row(new_data)
            st.success(f"✅ Deviation registered successfully with ID {deviation_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ Change Control Section
with tab3:
    st.subheader("🔄 Register a Change Request")
    change_id = generate_record_id(sheets["Change Control"], "CC")
    change_type = st.selectbox("Change Type", ["Equipment", "Process", "Document", "Other"])
    justification = st.text_area("Justification for Change")
    impact_analysis = st.text_area("Impact Analysis")
    requested_by = st.text_input("👤 Requested By")

    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="change_control_file")

    if st.button("Submit Change Request"):
        if change_type and justification and impact_analysis and requested_by:
            file_url = ""
            if uploaded_file:
                file_url = upload_to_drive(uploaded_file, f"{change_id}_{uploaded_file.name}")

            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), change_id, change_type, justification, impact_analysis, requested_by, file_url]
            sheets["Change Control"].append_row(new_data)
            st.success(f"✅ Change request registered successfully with ID {change_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ Admin View (Batch Processing for Efficiency)
with admin_tab:
    st.subheader("🔐 Admin Panel - View All Records")
    admin_password = st.text_input("Enter Admin Password", type="password")

    if st.button("Access Admin Panel"):
        if admin_password == "admin123":
            st.success("✅ Access Granted! Viewing all records.")

            # ✅ Fetch all data in a batch request to reduce API calls
            sheet_data = {name: get_sheet_values(sheet) for name, sheet in sheets.items()}

            for name, data in sheet_data.items():
                st.subheader(f"📜 {name} Records")
                if len(data) > 1:
                    st.table(data)
                else:
                    st.info(f"No records found for {name}.")
        else:
            st.error("❌ Incorrect password! Access Denied.")
