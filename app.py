import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# =========================
# Google Sheets Setup
# =========================
def get_gsheet_client():
    try:
        creds = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        }
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(creds, scopes=scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Error connecting to Google Sheets: {e}")
        st.stop()

# =========================
# Save Persona Function
# =========================
def save_persona_to_gsheet(persona):
    client = get_gsheet_client()
    try:
        sheet = client.open("prompts_generated").sheet1  # ✅ your sheet name
        sheet.append_row([
            persona["id"],
            persona["name"],
            persona["dob"],
            persona["profession"],
            persona["description"]
        ])
        st.success("✅ Persona saved successfully to Google Sheets!")
    except Exception as e:
        st.error(f"❌ Error saving persona: {e}")

# =========================
# Main Streamlit App
# =========================
st.set_page_config(page_title="Persona Generator", layout="centered")
st.title("📝 Character Persona Generator")

# Number of personas
num_personas = st.number_input("Enter number of personas (max 10):", min_value=1, max_value=10, value=1)

if "persona_inputs" not in st.session_state:
    st.session_state.persona_inputs = {}

# Keep session state synced
current_keys = list(st.session_state.persona_inputs.keys())
for key in current_keys:
    if int(key.split("_")[-1]) >= num_personas:
        del st.session_state.persona_inputs[key]

# Input fields
for i in range(int(num_personas)):
    if f"name_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"name_{i}"] = ""
    if f"dob_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"dob_{i}"] = ""
    if f"profession_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"profession_{i}"] = ""
    if f"description_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"description_{i}"] = ""

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
        all_personas.append(persona)
        save_persona_to_gsheet(persona)

    if all_personas:
        st.success("🎉 All personas saved!")

# =========================
# View Saved Data
# =========================
if st.button("📂 View All Personas in Sheet"):
    client = get_gsheet_client()
    sheet = client.open("prompts_generated").sheet1
    data = sheet.get_all_records()
    if data:
        st.dataframe(data)
    else:
        st.info("No personas saved yet.")
