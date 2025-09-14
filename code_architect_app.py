# PGE Code Architect: A Streamlit application for systematic, high-fidelity code generation.
# Inspired by the Perceptual Grid Engine (PGE) methodology.
# Date: September 14, 2025
#
# v5.5: Fixed Streamlit Rerun Loop
# - Removed unnecessary `st.rerun()` calls that caused the final code to
#   flash and disappear after a successful generation.
# - The control flow is now more stable and correctly displays the final state.

# --- Pre-run Setup ---
# Before running, you may need to install the 'requests' library:
# pip install requests

import streamlit as st
import requests
import json
import time

# --- Configuration ---
API_KEY = ""
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"

# --- Helper Functions ---
def make_gemini_request(system_prompt, user_prompt, retries=2, delay=20):
    """Sends a request to the Gemini API using a direct HTTP POST request with retries."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
        "generationConfig": {
            "temperature": 0.4,
            "topP": 1,
            "topK": 32,
            "maxOutputTokens": 8192,
        },
    }

    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            
            response_json = response.json()
            candidate = response_json.get('candidates', [{}])[0]
            content_part = candidate.get('content', {}).get('parts', [{}])[0]
            result_text = content_part.get('text', '')

            if not result_text:
                st.warning("API returned an empty response.")
                return "Error: Empty response from API."

            time.sleep(1)
            return result_text

        except requests.exceptions.RequestException as e:
            st.warning(f"API Request failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                st.error("API request failed after multiple retries.")
                return f"Error: {e}"
        except (KeyError, IndexError) as e:
            st.error(f"Failed to parse API response. Error: {e}")
            st.json(response.json())
            return "Error: Could not parse API response."
            
    return "Error: API request failed after all retries."

# --- AI-Powered Summarizer ---
def summarize_code_block(code_block):
    """Uses the AI to create an intelligent summary of a code block for long-term memory."""
    system_prompt = "You are a senior code analyst. Your task is to summarize the provided Python code block. Focus on the core functionality, key function names, and variable definitions. Your summary must be a single, dense, and concise sentence."
    user_prompt = f"Please summarize this code block:\n\n```python\n{code_block}\n```"
    summary = make_gemini_request(system_prompt, user_prompt)
    if summary.startswith("Error:"):
        return f"{code_block.splitlines()[0]}\n{code_block[:250]}...\n\n"
    return summary

# --- PGE Core Functions ---
def pge_step_1_planning(master_prompt):
    """PGE Step 1: Analyze the master prompt and create a detailed, structured plan."""
    st.info("Architectural Planning Initiated...")
    with st.spinner("Step 1: Analyzing prompt and creating a structural plan..."):
        system_prompt = "You are a world-class software architect. Your task is to break down a prompt for a SINGLE-FILE application into a logical sequence of code sections. Your plan MUST be a JSON object with a single root key named 'plan', containing a list of objects. Each object must have two keys: 'section_name' and 'description'. CRITICAL RULES: 1. For each section's 'description', you MUST explicitly extract and include any specific, critical requirements from the master prompt that are relevant to that section. 2. For example, if the prompt mentions a specific dictionary key or a UI element, that detail must be in the description for the relevant section. 3. Think sequentially for a single script: Imports -> Constants/Setup -> Functions/Classes -> Main execution logic. 4. The output must be ONLY the raw JSON object."
        user_prompt = f"Here is the detailed project request for a single-file application:\n\n---\n\n{master_prompt}\n\n---\n\nPlease create the JSON development plan."

        response_text = make_gemini_request(system_prompt, user_prompt)
        if response_text.startswith("Error:"): return None
        try:
            clean_response = response_text.strip().replace("```json", "").replace("```", "").strip()
            plan = json.loads(clean_response)
            st.session_state.architect_plan = plan.get("plan", [])
            st.success("✔ Step 1: Detailed Structural Plan created.")
            with st.expander("View Generated Plan", expanded=False): st.json(plan)
            return st.session_state.architect_plan
        except json.JSONDecodeError:
            st.error("Error decoding the structural plan from the model.")
            st.text_area("Model Response to Debug", response_text, height=300)
            return None

def pge_step_2_generation_loop(plan, recent_sections_to_keep=2):
    """PGE Step 2: Iterate through plan, generate code with hybrid memory."""
    st.info("Code Generation Initiated...")
    long_term_memory = ""
    short_term_memory_blocks = []
    all_code_blocks = []

    progress_bar = st.progress(0, text="Starting code generation...")
    for i, step in enumerate(plan):
        section_name = step.get("section_name", f"S{i+1}")
        description = step.get("description", "")
        progress_text = f"Step {i+1}/{len(plan)}: Gen `{section_name}`..."
        progress_bar.progress((i + 1) / len(plan), text=progress_text)

        with st.status(f"Generating Section: `{section_name}`", expanded=False) as status:
            system_prompt = "You are an expert Python programmer. Your task is to write a clean and functional block of code for a specific section of a larger script. CRITICAL RULES: 1. You MUST ONLY output the raw code for the requested section. 2. Do NOT include any explanations, comments, or markdown formatting like ```python ... ```. 3. Use the Long-Term and Short-Term memory to ensure your code is consistent with previously written code. 4. Ensure the code is complete for the given section. Do not use placeholders."
            short_term_context = "\n\n".join(short_term_memory_blocks) if short_term_memory_blocks else "N/A"
            user_prompt = f"**Long-Term Memory:**\n{long_term_memory or 'N/A'}\n---\n**Short-Term Memory:**\n{short_term_context}\n---\n**Current Task:** `{section_name}`\n**Instructions:** {description}"
            
            generated_code = make_gemini_request(system_prompt, user_prompt)
            if generated_code.startswith("Error:"):
                st.session_state.generation_failed = True
                return None

            clean_code = generated_code.strip().replace("```python", "").replace("```", "").strip()
            full_block = f"# --- SECTION: {section_name.upper()} ---\n{clean_code}\n"
            all_code_blocks.append(full_block)

            short_term_memory_blocks.append(full_block)
            if len(short_term_memory_blocks) > recent_sections_to_keep:
                block_to_summarize = short_term_memory_blocks.pop(0)
                summary = summarize_code_block(block_to_summarize)
                long_term_memory += f"- {summary}\n"
            status.update(label=f"✔ Section `{section_name}` generated.", state="complete")

    progress_bar.empty()
    st.success("✔ Initial Code Generation Completed.")
    return "\n".join(all_code_blocks)

def pge_step_3_refinement(generated_code, master_prompt):
    """PGE Step 3: Review the complete code against the prompt and correct errors."""
    st.info("Self-Correction and Refinement Initiated...")
    with st.spinner("Step 3: Performing final review and correcting the full script..."):
        system_prompt = "You are a Senior Software Engineer performing a final code review. Your task is to refine the provided script to perfection. CRITICAL RULES: 1. Analyze the user's original prompt and the complete generated script. 2. Correct any bugs, logical errors, or inconsistencies. 3. Remove any redundant or nonsensical code (e.g., incorrect `if __name__ == '__main__'` blocks, duplicate UI elements). 4. Ensure the code is 100% compliant with all requirements in the original prompt. 5. Your final output MUST be ONLY the raw, complete, and corrected Python code. Do not add any explanations or markdown."
        user_prompt = f"**Original Prompt:**\n{master_prompt}\n---\n**Script to Correct:**\n```python\n{generated_code}\n```"
        
        corrected_code = make_gemini_request(system_prompt, user_prompt)
        if corrected_code.startswith("Error:"):
            st.error("Self-correction step failed. Returning uncorrected code.")
            return generated_code

        clean_code = corrected_code.strip().replace("```python", "").replace("```", "").strip()
        st.success("✔ Step 3: Self-Correction Completed.")
        return clean_code

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="PGE Single-File Architect")

# Initialize session state variables
if 'final_code' not in st.session_state: st.session_state.final_code = ""
if 'generation_failed' not in st.session_state: st.session_state.generation_failed = False
if 'start_generation' not in st.session_state: st.session_state.start_generation = False
if 'master_prompt' not in st.session_state: st.session_state.master_prompt = ""

st.title("🏗️ PGE Single-File Architect v5.5")
st.markdown("An AI assistant with self-correction and intelligent memory.")
st.markdown("---")

with st.sidebar:
    st.header("🧠 Memory Settings")
    recent_sections_to_keep = st.slider("Short-Term Memory Window", 1, 5, 2, 1)
    st.markdown("---")
    st.header("How It Works")
    st.markdown("""1.  **Plan:** Creates a detailed plan.\n2.  **Generate:** Writes code section-by-section.\n3.  **Refine:** Performs a final "self-correction" pass.""")

col1, col2 = st.columns([1.5, 2])
with col1:
    st.subheader("1. Master Prompt")
    master_prompt_input = st.text_area("Enter your detailed prompt...", height=400, key="prompt_input")

    if st.button("Generate Application", use_container_width=True, disabled=(not master_prompt_input)):
        st.session_state.final_code = ""
        st.session_state.generation_failed = False
        st.session_state.architect_plan = []
        st.session_state.master_prompt = master_prompt_input
        st.session_state.start_generation = True
        st.rerun()

# --- Main Process Controller (CORRECTED LOGIC) ---
if st.session_state.start_generation:
    # This block now runs on the rerun triggered by the button
    plan = pge_step_1_planning(st.session_state.master_prompt)
    if plan:
        generated_code = pge_step_2_generation_loop(plan, recent_sections_to_keep)
        if generated_code:
            final_code = pge_step_3_refinement(generated_code, st.session_state.master_prompt)
            st.session_state.final_code = final_code
    
    # Reset the trigger AFTER the entire process is complete
    st.session_state.start_generation = False
    # DO NOT rerun here. Let the script finish its run to display the code.

with col2:
    st.subheader("2. Final Application Code")
    if st.session_state.final_code and not st.session_state.generation_failed:
        st.code(st.session_state.final_code, language='python', line_numbers=True)
        st.download_button("💾 Download .py file", st.session_state.final_code, "generated_app.py", "text/python")
    else:
        st.info("Your generated application script will appear here.")
