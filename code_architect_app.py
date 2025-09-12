# PGE Code Architect: A Streamlit application for systematic, high-fidelity code generation.
# Inspired by the Perceptual Grid Engine (PGE) methodology.
# Date: September 10, 2025
# Location: Oregon City, Oregon
#
# v4.1: Removed the streamlit-extras dependency to resolve ModuleNotFoundError.
# - Replaced add_vertical_space() with st.markdown for cleaner code.
# - The application is now self-contained with only core libraries.

import streamlit as st
import google.generativeai as genai
import json
import time

# --- Configuration ---
# To make this easier to use, the API key is handled via Streamlit's secrets management.
# For local development:
# 1. Create a folder named `.streamlit` in your project directory.
# 2. Inside it, create a file named `secrets.toml`.
# 3. Add your key to that file like this: API_KEY = "YOUR_GOOGLE_AI_API_KEY_HERE"
#
# For Streamlit Community Cloud deployment, you can set the secret directly in the app's settings.
try:
    API_KEY = st.secrets["API_KEY"]
    genai.configure(api_key=API_KEY)
except (FileNotFoundError, KeyError):
    st.warning("API_KEY not found in st.secrets. Please provide your key in the sidebar for this session.")
    API_KEY = ""


# --- AI Model Setup ---
def get_model(api_key_from_input):
    """Initializes the model with the provided API key."""
    try:
        if not api_key_from_input:
            return None
        genai.configure(api_key=api_key_from_input)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        return model
    except Exception as e:
        st.error(f"Failed to initialize the AI model. Error: {e}")
        return None

# --- Helper Functions ---
def make_gemini_request(model, system_prompt, user_prompt, retries=2, delay=20):
    """Sends a request to the Gemini API using the official SDK with retries."""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    for attempt in range(retries):
        try:
            response = model.generate_content(full_prompt)
            # Add a small delay after a successful request to respect rate limits
            time.sleep(2)
            return response.text
        except Exception as e:
            st.warning(f"API Request failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error("API request failed after multiple retries.")
                return f"Error: {e}"
    return "Error: API request failed after all retries."

# --- PGE Core Functions ---
def pge_step_1_planning(model, master_prompt):
    """PGE Step 1: Analyze the master prompt and create a structured plan for a single file."""
    st.info("Architectural Planning Initiated...")
    with st.spinner("Step 1: Analyzing prompt and creating a structural plan for the script..."):
        system_prompt = """
You are a world-class software architect. Your task is to break down a prompt for a SINGLE-FILE application into a logical sequence of code sections.
Your plan MUST be a JSON object. The JSON object should have a single root key named "plan".
The "plan" key should contain a list of objects, where each object represents a logical section of the code, like 'Imports', 'Global Variables', 'Helper Functions', 'Main Class Definition', 'Streamlit UI Layout', 'Execution Block'.
Each object must have two keys: "section_name" and "description".
- "section_name": The name of the code section (e.g., "Imports", "Helper Functions").
- "description": A concise, step-by-step instruction for the coding AI on what specific code to write for THIS section.

CRITICAL RULES:
1. Think sequentially and logically for a single script. Start with imports, then constants/setup, then functions/classes, and finally the main execution logic.
2. The output must be ONLY the raw JSON object, without any surrounding text or markdown formatting.
        """
        user_prompt = f"Here is the detailed project request for a single-file application:\n\n---\n\n{master_prompt}\n\n---\n\nPlease create the JSON development plan."

        response_text = make_gemini_request(model, system_prompt, user_prompt)
        if response_text.startswith("Error:"):
            st.error(f"Failed to create plan: {response_text}")
            return None
        try:
            clean_response = response_text.strip().replace("```json", "").replace("```", "").strip()
            plan = json.loads(clean_response)
            st.session_state.architect_plan = plan.get("plan", [])
            st.success("✔ Step 1: Structural Plan created successfully.")
            with st.expander("View Generated Plan", expanded=False):
                st.json(plan)
            return st.session_state.architect_plan
        except json.JSONDecodeError as e:
            st.error(f"Error decoding the structural plan. The model's response was not valid JSON. Error: {e}")
            st.text_area("Model Response to Debug", response_text, height=300)
            return None

def pge_step_2_generation_loop(model, plan):
    """PGE Step 2 & 3: Iterate through the plan and generate code for each section, assembling a single script."""
    st.info("Code Generation Initiated...")
    cumulative_memory = ""
    st.session_state.final_code = ""
    all_code_blocks = []

    total_steps = len(plan)
    progress_bar = st.progress(0, text="Starting code generation...")

    for i, step in enumerate(plan):
        section_name = step.get("section_name", f"Section {i+1}")
        description = step.get("description", "")
        progress_text = f"Step {i+1}/{total_steps}: Generating Section: `{section_name}`..."
        progress_bar.progress((i + 1) / total_steps, text=progress_text)

        with st.status(progress_text, expanded=False) as status:
            system_prompt = """
You are an expert Python programmer. Your task is to write a clean and functional block of code for a specific section of a larger script.
CRITICAL RULES:
1. You MUST ONLY output the raw code for the requested section.
2. Do NOT include any explanations, comments about your own code, or markdown formatting like ```python ... ```.
3. Use the "Cumulative Memory" of previously written sections to ensure your code is consistent and compatible.
4. Ensure the code is complete for the given section. Do not use placeholders.
            """
            user_prompt = f"""
**Project Context (Cumulative Memory of previously generated sections):**
---
{cumulative_memory if cumulative_memory else "This is the first section of the script."}
---
**Current Task:**
Write the complete code for the section named `{section_name}`.
**Instructions for this section:**
{description}
            """
            generated_code = make_gemini_request(model, system_prompt, user_prompt)
            if generated_code.startswith("Error:"):
                st.error(f"Failed to generate code for section `{section_name}`: {generated_code}")
                status.update(label=f"Error generating `{section_name}`", state="error")
                st.session_state.generation_failed = True
                return

            clean_code = generated_code.strip().replace("```python", "").replace("```", "").strip()

            # Add a header comment for clarity in the final script
            header = f"# --- SECTION: {section_name.upper()} ---"
            full_block = f"{header}\n{clean_code}\n"
            all_code_blocks.append(full_block)

            memory_entry = f"Section: `{section_name}` was just written.\n--- Summary ---\n{clean_code[:300]}...\n\n"
            cumulative_memory += memory_entry

            status.update(label=f"✔ Successfully generated `{section_name}`", state="complete")

    progress_bar.empty()
    st.session_state.final_code = "\n".join(all_code_blocks)
    st.success("✔ Code Generation Completed.")

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="PGE Single-File Architect")

if 'architect_plan' not in st.session_state: st.session_state.architect_plan = []
if 'final_code' not in st.session_state: st.session_state.final_code = ""
if 'generation_failed' not in st.session_state: st.session_state.generation_failed = False
if 'api_key_valid' not in st.session_state: st.session_state.api_key_valid = bool(API_KEY)


st.title("🏗️ PGE Single-File Architect")
st.markdown("An AI assistant that systematically generates complete, single-file applications from a detailed prompt.")
st.markdown("---")

# Sidebar for API Key Input if not in secrets
with st.sidebar:
    st.header("Configuration")
    if not API_KEY:
        sidebar_api_key = st.text_input("Enter your Google AI API Key", type="password", help="Get your key from Google AI Studio.")
        if sidebar_api_key:
            st.session_state.api_key_valid = True
            st.session_state.model = get_model(sidebar_api_key)
        else:
            st.session_state.api_key_valid = False
    else:
        st.success("API Key loaded from secrets.")
        st.session_state.model = get_model(API_KEY)

    # Replaced streamlit-extras with simple markdown for spacing
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.header("How It Works")
    st.markdown("""
    1.  **Plan:** The Architect analyzes your prompt and creates a structural plan for the script (Imports, Functions, UI, etc.).
    2.  **Generate:** It writes the code for each section, using a 'Cumulative Memory' to ensure all parts work together.
    3.  **Assemble:** It combines all generated sections into a single, complete script for you to use.
    """)


col1, col2 = st.columns([1.5, 2])
with col1:
    st.subheader("1. Master Prompt")
    master_prompt = st.text_area("Enter your detailed prompt for a single-file application...", height=400, placeholder="Example: Create a simple Streamlit app that converts Celsius to Fahrenheit. It should have a title, a number input for Celsius, and display the result.")

    if st.button("Generate Application", use_container_width=True, disabled=(not master_prompt or not st.session_state.api_key_valid)):
        st.session_state.architect_plan = []
        st.session_state.final_code = ""
        st.session_state.generation_failed = False
        if st.session_state.get('model'):
            plan = pge_step_1_planning(st.session_state.model, master_prompt)
            if plan:
                pge_step_2_generation_loop(st.session_state.model, plan)
        else:
            st.error("API Model not initialized. Please check your API Key.")


with col2:
    st.subheader("2. Generated Application Code")

    if not st.session_state.final_code:
        st.info("Your generated application script will appear here.")

    if st.session_state.final_code and not st.session_state.generation_failed:
        st.code(st.session_state.final_code, language='python', line_numbers=True)

        st.download_button(
            label="💾 Download as .py file",
            data=st.session_state.final_code,
            file_name="generated_app.py",
            mime="text/python",
            use_container_width=True
        )

st.markdown("---")
st.markdown("Built with the Perceptual Grid Engine (PGE) concept.")

