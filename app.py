import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
from pypdf import PdfReader
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# 1. Google GenAI API Setup
# -----------------------------
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Error configuring Google GenAI API: {e}")
    st.stop()

# -----------------------------
# 2. Google Sheets Setup
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)

    # open sheet (or create new if not provided)
    SHEET_URL = st.secrets.get("SHEET_URL", None)
    if SHEET_URL:
        sheet = client.open_by_url(SHEET_URL).sheet1
    else:
        sheet = client.create("Character_Personas").sheet1

    # Add header if sheet empty
    if not sheet.get_all_values():
        sheet.append_row(["ID", "Name", "DOB", "Profession", "Description", "Prompt", "Created At"])

except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

# -----------------------------
# 3. Load Few-Shot Examples from PDFs
# -----------------------------
pdf_files = [
    r"C:\Users\somas\Downloads\Prompts-Sreshta (2).pdf",
    r"C:\Users\somas\Downloads\Prompts-Sreshta (1).pdf",
    r"C:\Users\somas\Downloads\Prompts-Sreshta.pdf"
]

few_shot_examples_text = ""
for pdf_file in pdf_files:
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text() or ""
            few_shot_examples_text += text
    except Exception as e:
        st.warning(f"Skipping {pdf_file}: {e}")

# -----------------------------
# 4. Prompt Template
# -----------------------------
base_prompt_template = """
Generate a detailed character persona based on the provided name and profession, 
using the following examples as a guide for structure and content.

{few_shot_examples}

Generate Persona for:
Name: {name}
Profession: {profession}
"""

few_shot_prompt = base_prompt_template.format(
    few_shot_examples=few_shot_examples_text,
    name="{name}",
    profession="{profession}"
)

# -----------------------------
# 5. Helper Functions
# -----------------------------
def clean_prompt(text: str) -> str:
    text = re.sub(r"\*\*", "", text)
    return text.replace("\n", " ").strip()

def generate_description_from_api(name: str, persona_text: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        desc_prompt = f"""
        Summarize the personality of {name} in one sentence.
        Be concise, professional, and descriptive.
        Example: "Rana is disciplined, dependable, strategic, and result-oriented leader."
        
        Persona details:
        {persona_text}
        """
        response = model.generate_content(desc_prompt)
        return response.text.strip()
    except Exception:
        return "Description not available."

def generate_character_persona(name, profession):
    if not name or not profession:
        return "Error: Name and Profession are required."

    prompt_for_api = few_shot_prompt.format(name=name, profession=profession)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt_for_api)
        return response.text
    except Exception as e:
        return f"An error occurred during API call: {e}"

def process_character(idx, name, dob, profession, persona_text):
    prompt = clean_prompt(persona_text)
    description = generate_description_from_api(name, prompt)
    return {
        "id": idx,
        "name": name,
        "dob": dob,
        "prompt": prompt,
        "description": description,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": profession
    }

# -----------------------------
# 6. Streamlit UI
# -----------------------------
st.title("Character Persona Generator")

num_personas = st.number_input("Enter number of personas (max 100):", min_value=1, max_value=100, value=1)

if "persona_inputs" not in st.session_state:
    st.session_state.persona_inputs = {}

# maintain persona input fields
current_keys = list(st.session_state.persona_inputs.keys())
for key in current_keys:
    if int(key.split("_")[-1]) >= num_personas:
        del st.session_state.persona_inputs[key]

for i in range(int(num_personas)):
    if f"name_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"name_{i}"] = ""
    if f"dob_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"dob_{i}"] = ""
    if f"profession_{i}" not in st.session_state.persona_inputs:
        st.session_state.persona_inputs[f"profession_{i}"] = ""

with st.container():
    for i in range(int(num_personas)):
        st.subheader(f"Character {i + 1}")
        st.session_state.persona_inputs[f"name_{i}"] = st.text_input(
            f"Name for character {i + 1}:", key=f"name_input_{i}", value=st.session_state.persona_inputs[f"name_{i}"]
        )
        st.session_state.persona_inputs[f"dob_{i}"] = st.text_input(
            f"Date of Birth for character {i + 1}:", key=f"dob_input_{i}", value=st.session_state.persona_inputs[f"dob_{i}"]
        )
        st.session_state.persona_inputs[f"profession_{i}"] = st.text_input(
            f"Profession for character {i + 1}:", key=f"profession_input_{i}", value=st.session_state.persona_inputs[f"profession_{i}"]
        )

generate_button = st.button("Generate Personas")

if generate_button:
    all_personas_data = []
    for i in range(int(num_personas)):
        name = st.session_state.persona_inputs.get(f"name_{i}", "")
        dob = st.session_state.persona_inputs.get(f"dob_{i}", "")
        profession = st.session_state.persona_inputs.get(f"profession_{i}", "")

        if not name or not profession:
            st.warning(f"Skipping Character {i+1}: Name and Profession required.")
            continue

        persona_text = generate_character_persona(name, profession)
        character_row = process_character(i + 1, name, dob, profession, persona_text)
        all_personas_data.append(character_row)

    if all_personas_data:
        st.subheader("Generated Personas")
        for persona_data in all_personas_data:
            st.write(f"**ID:** {persona_data['id']}")
            st.write(f"**Name:** {persona_data['name']}")
            st.write(f"**DOB:** {persona_data['dob']}")
            st.write(f"**Profession:** {persona_data['category']}")
            st.write(f"**Description:** {persona_data['description']}")
            st.write(f"**Prompt:** {persona_data['prompt']}")
            st.write("---")

        # --- Save to Google Sheets ---
        try:
            for persona_data in all_personas_data:
                sheet.append_row([
                    persona_data["id"],
                    persona_data["name"],
                    persona_data["dob"],
                    persona_data["category"],
                    persona_data["description"],
                    persona_data["prompt"],
                    persona_data["created_at"]
                ])
            st.success("✅ Personas saved to Google Sheets successfully!")
        except Exception as e:
            st.error(f"Error saving to Google Sheets: {e}")
