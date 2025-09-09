import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ----------------------
# GOOGLE SHEETS SETUP
# ----------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials.json
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)

# Spreadsheet file name
SHEET_NAME = "prompts_generated"

try:
    sheet = client.open(SHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    st.error(f"Spreadsheet '{SHEET_NAME}' not found. Please check the name in Google Drive.")
    st.stop()

# ----------------------
# STREAMLIT APP
# ----------------------
st.set_page_config(page_title="Character Persona Generator", layout="centered")
st.title("📝 Character Persona Generator")

# Input: Number of personas
num_personas = st.number_input("Enter number of personas (max 10):", min_value=1, max_value=10, value=1)

if "persona_inputs" not in st.session_state:
    st.session_state.persona_inputs = {}

# Sync session state
current_keys = list(st.session_state.persona_inputs.keys())
for key in current_keys:
    if int(key.split("_")[-1]) >= num_personas:
        del st.session_state.persona_inputs[key]

# Create input fields
for i in range(int(num_personas)):
    if f"name_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"name_{i}"] = ""
    if f"dob_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"dob_{i}"] = ""
    if f"profession_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"profession_{i}"] = ""
    if f"description_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"description_{i}"] = ""

# Form for multiple personas
with st.form("persona_form"):
    for i in range(int(num_personas)):
        st.subheader(f"Character {i+1}")
        st.session_state.persona_inputs[f"name_{i}"] = st.text_input(
            f"Name {i+1}", value=st.session_state.persona_inputs[f"name_{i}"]
        )
        st.session_state.persona_inputs[f"dob_{i}"] = st.text_input(
            f"Date of Birth {i+1}", value=st.session_state.persona_inputs[f"dob_{i}"]
        )
        st.session_state.persona_inputs[f"profession_{i}"] = st.text_input(
            f"Profession {i+1}", value=st.session_state.persona_inputs[f"profession_{i}"]
        )
        st.session_state.persona_inputs[f"description_{i}"] = st.text_area(
            f"Description {i+1}", value=st.session_state.persona_inputs[f"description_{i}"]
        )

    submitted = st.form_submit_button("💾 Save All Personas")

# ----------------------
# Save personas to Google Sheets
# ----------------------
def save_persona_to_sheet(persona):
    """Append a single persona to the Google Sheet."""
    try:
        sheet.append_row([
            persona["id"],
            persona["name"],
            persona["dob"],
            persona["profession"],
            persona["description"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
        return True
    except Exception as e:
        st.error(f"❌ Error saving persona: {e}")
        return False

if submitted:
    all_personas = []
    for i in range(int(num_personas)):
        name = st.session_state.persona_inputs[f"name_{i}"]
        dob = st.session_state.persona_inputs[f"dob_{i}"]
        profession = st.session_state.persona_inputs[f"profession_{i}"]
        description = st.session_state.persona_inputs[f"description_{i}"]

        if not name or not profession:
            st.warning(f"⚠️ Skipping Character {i+1}: Name and Profession required.")
            continue

        persona = {
            "id": i + 1,
            "name": name,
            "dob": dob,
            "profession": profession,
            "description": description,
        }
        if save_persona_to_sheet(persona):
            all_personas.append(persona)

    if all_personas:
        st.success(f"🎉 Saved {len(all_personas)} personas to Google Sheets!")

# ----------------------
# Display all saved personas
# ----------------------
if st.button("📂 View All Personas in Sheet"):
    try:
        data = sheet.get_all_records()
        if data:
            st.dataframe(data)
        else:
            st.info("No personas saved yet.")
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
