🏗️ PGE Code Architect
PGE Code Architect is a Streamlit application that systematically generates complete, single-file Python scripts from a detailed prompt. It is a direct and practical implementation of the Perceptual Grid Engine (PGE) methodology, designed to solve the critical challenges of consistency and coherency in long-form generative tasks.

Unlike traditional AI assistants that attempt to generate an entire script in a single, "holistic" pass, this application breaks the task down into a structured, multi-step process. This approach ensures a higher degree of accuracy and reliability in the final output.

✨ Features
PGE-Powered Generation: This is a live demonstration of the Perceptual Grid Engine concept applied to code.

Systematic Planning: The AI first acts as an "Architect," creating a detailed, logical plan (a "grid") for the entire application.

Cumulative Memory: It then writes each section of the code sequentially, using a "cumulative memory" of previously generated sections to ensure consistency and prevent logical inconsistencies.

Robust & Reliable: The application is built with error handling and retry logic to gracefully manage API requests and ensure a smooth user experience.

Single-File Output: The final output is a single, complete, and runnable Python script, ready for immediate use.

🚀 Getting Started
Prerequisites
To run this application, you'll need Python installed on your system. It's recommended to use a virtual environment.

Python 3.8+

Installation
Clone the repository:

git clone [https://github.com/your-username/pge-code-architect.git](https://github.com/your-username/pge-code-architect.git)
cd pge-code-architect

Install the required libraries:
Create a requirements.txt file in your project directory with the following content:

streamlit
google-generativeai

Then, install them using pip:

pip install -r requirements.txt

Configuration
The application requires a Google AI API Key. The most secure and recommended way to provide this is by using Streamlit's secrets management.

Create a folder named .streamlit in your project's root directory.

Inside it, create a file named secrets.toml.

Add your API key to that file in the format below:

API_KEY = "YOUR_GOOGLE_AI_API_KEY_HERE"

(For local testing, you can also paste your key directly into the application's sidebar.)

Running the Application
Once you have installed the dependencies and configured your API key, you can launch the app from your terminal:

streamlit run app.py

🛠 How It Works: The PGE in Action
The application orchestrates a three-step process, directly implementing the PGE methodology for long-form text generation.

Planning Phase (The Architect): The user's prompt is sent to the AI with a strict instruction to return a JSON object containing a sequential plan for the script. This plan acts as the "grid" that structures the entire process.

Generation Phase (The Author): The application enters a loop, requesting code for each section outlined in the plan.

Assembly Phase (The Cumulative Memory): With each request, the prompt includes a cumulative memory—a summary of all code generated in previous steps. This ensures that the AI writes code that is fully compatible with what has already been created, preventing logical errors and guaranteeing a single, coherent script at the end.

This systematic process replaces the unpredictable nature of single-pass generation with a structured, transparent, and more reliable alternative.
