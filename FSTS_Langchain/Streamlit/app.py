
# --- Standard Library Imports ---
import os
import tempfile
from pathlib import Path
import shutil
from typing import List

# --- Streamlit for Web UI ---
import streamlit as st

# --- CrewAI and LangChain Imports ---
from crewai import Agent, Task, Crew, Process
from crewai import LLM
from crewai.project import CrewBase, agent, crew, task
from langchain_community.llms import HuggingFaceHub
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# --- PDF and Markdown Handling ---
from fpdf import FPDF
from markdown2 import Markdown

# --- PDF Reading ---
import PyPDF2

# --- Warnings ---
import warnings
warnings.filterwarnings('ignore')

# Import the modularized crew runner
from crew_runner import run_crew


# --- Inject Bootstrap CSS ---
st.set_page_config(page_title="ABAP Crew Spec Generator", layout="wide")
# --- Inject Bootstrap and custom CSS from external file ---
st.set_page_config(page_title="ABAP Crew Spec Generator", layout="wide")
# Inject Bootstrap CDN
st.markdown(
    '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" crossorigin="anonymous">',
    unsafe_allow_html=True
)
# Inject custom CSS from file
with open("frontend_bootstrap.css", "r", encoding="utf-8") as css_file:
    custom_css = css_file.read()
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/5968/5968705.png", width=80
    )
    st.markdown(
        """
        ## About
        This tool generates beautiful, business-ready **Functional & Technical Specifications** from your ABAP code and a template PDF using advanced AI agents.
        
        - Upload your ABAP `.txt` files and a template PDF.
        - Click **Generate Specifications**.
        - Review and download the generated documentation.
        """
    )
    st.markdown("---")
    st.markdown(
        """
        **Developed with ❤️ using CrewAI, LangChain, and Google Gemini.**
        """
    )


# --- Main Title and Instructions with Bootstrap ---
st.markdown(
    '''
    <div class="container-fluid">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="bootstrap-card">
            <div class="bootstrap-title text-center">FS/TS GenAI Platform</div>
            <div class="bootstrap-subtitle">Upload your ABAP code files and a template PDF to generate professional functional and technical specifications in seconds.</div>
            <div class="row g-4">
              <div class="col-md-6">
                <div class="card p-3 border-0">
                  <h6 class="mb-2 text-dark">ABAP Code Files (.txt)</h6>
                  <div id="code-upload"></div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="card p-3 border-0">
                  <h6 class="mb-2 text-dark">Template PDF</h6>
                  <div id="pdf-upload"></div>
                </div>
              </div>
            </div>
            <div class="d-flex justify-content-center mt-4">
              <div id="generate-btn"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    ''', unsafe_allow_html=True
)

# --- Place Streamlit widgets into Bootstrap containers using empty() ---
code_upload_placeholder = st.empty()
pdf_upload_placeholder = st.empty()
btn_placeholder = st.empty()

with code_upload_placeholder.container():
    code_files = st.file_uploader(
        "Upload ABAP code files (.txt)",
        type=["txt"],
        accept_multiple_files=True,
        help="Upload one or more .txt files containing ABAP code."
    )
with pdf_upload_placeholder.container():
    template_pdf = st.file_uploader(
        "Upload Template PDF",
        type=["pdf"],
        help="Upload the template PDF file."
    )
with btn_placeholder.container():
    generate_btn = st.button("✨ Generate Specifications", key="generate_btn", use_container_width=True)

if generate_btn:
    if not code_files or not template_pdf:
        st.error("Please upload at least one code file and a template PDF.")
    else:
        with st.spinner("Processing and generating your documentation..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                code_dir = os.path.join(tmpdir, "code_files")
                os.makedirs(code_dir, exist_ok=True)
                # Save code files
                for file in code_files:
                    file_path = os.path.join(code_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                # Save template PDF
                template_pdf_path = os.path.join(tmpdir, "template.pdf")
                with open(template_pdf_path, "wb") as f:
                    f.write(template_pdf.read())
                # Run the crew logic
                result_markdown = run_crew(code_dir, template_pdf_path)
        # Display the result
        st.markdown("---")
        st.markdown(
            '<div class="container-fluid"><div class="row justify-content-center"><div class="col-lg-8"><div class="card p-4 border-0 mb-4" style="background:#f9fafb;color:#222;"><div style="font-size:1.3rem;font-weight:600;color:#222;margin-bottom:1rem;">Generated Specifications</div></div></div></div></div>',
            unsafe_allow_html=True
        )
        st.markdown(result_markdown, unsafe_allow_html=True)
        # Optionally, add PDF conversion and download
        # (You can use your convert_markdown_to_pdf function here)
        # For demonstration, we skip PDF generation
        # st.download_button("Download PDF", data=pdf_bytes, file_name="output.pdf")
