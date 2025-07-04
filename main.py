import os
import tempfile
import re
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq
from pylatex import Document
from pylatex.utils import NoEscape

# Load API key from .env
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Streamlit page setup
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# UI Styles
st.markdown("""
<style>
body { background-color: #0f172a; color: #f1f5f9; }
.stApp { font-family: 'Segoe UI', sans-serif; animation: fadeIn 1s ease-in-out; }
@keyframes fadeIn { 0% { opacity: 0; transform: translateY(-10px); } 100% { opacity: 1; transform: translateY(0); } }
.stButton > button { background-color: #0ea5e9; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; transition: 0.2s ease-in-out; }
.stButton > button:hover { background-color: #0284c7; }
.stTextArea textarea { background-color: #1e293b; color: #f8fafc; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Optimizer with LaTeX Format")
st.write("Upload your resume, select a target role, and get a rewritten version tailored for that role in LaTeX-formatted PDF.")

job_role = st.selectbox("Select Target Job Role", [
    "Web Developer", "Data Scientist", "UI/UX Designer", "Software Engineer",
    "Marketing Analyst", "Product Manager", "Business Analyst",
    "Cybersecurity Analyst", "DevOps Engineer", "AI/ML Engineer"
])

uploaded_pdf = st.file_uploader("Upload Your Resume PDF", type=["pdf"])


# ✅ Sanitize LaTeX text
def sanitize_latex(text: str) -> str:
    # Replace markdown bold/italics with LaTeX
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", text)

    # Escape LaTeX characters
    replacements = {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"
    }
    for key, val in replacements.items():
        text = text.replace(key, val)

    # Remove generic AI phrases
    text = re.sub(r"(Note:|Let me know.*|This summary.*|In this rewritten.*)", "", text, flags=re.IGNORECASE)

    return text.strip()


# 🧱 Build LaTeX Template
def build_resume_latex(summary, education, projects, experience):
    return rf"""
\documentclass[11pt]{{article}}
\usepackage[margin=1in]{{geometry}}
\usepackage[breaklinks=true]{{hyperref}}
\usepackage{{fontspec}}
\usepackage{{fancyhdr}}
\usepackage{{enumitem}}
\pagestyle{{fancy}}
\renewcommand{{\headrulewidth}}{{0pt}}

\begin{{document}}

\section*{{Summary}}
{summary}

\section*{{Education}}
{education}

\section*{{Projects}}
{projects}

\section*{{Experience}}
{experience}

\end{{document}}
"""


# 📄 Compile PDF
def generate_pdf_from_latex(latex_body: str, filename: str):
    try:
        doc = Document(documentclass='article', document_options=['10pt', 'a4paper'])
        doc.packages.append(NoEscape(r'\usepackage[margin=1in]{geometry}'))
        doc.packages.append(NoEscape(r'\usepackage{enumitem}'))
        doc.packages.append(NoEscape(r'\usepackage{parskip}'))
        doc.packages.append(NoEscape(r'\usepackage{hyperref}'))
        doc.append(NoEscape(latex_body))

        pdf_path = os.path.join(tempfile.gettempdir(), filename)
        doc.generate_pdf(filepath=pdf_path, clean_tex=True, compiler='pdflatex')
        return f"{pdf_path}.pdf"

    except Exception as e:
        st.error(f"❌ Error compiling LaTeX: {e}")
        return None


# 🚀 Main Workflow
if uploaded_pdf and job_role:
    try:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = "".join([p.extract_text() or "" for p in reader.pages])
        st.success("✅ Resume uploaded and text extracted.")
        with st.expander("🔍 View Extracted Resume Text"):
            st.text(resume_text)

        with st.spinner("🔍 Extracting and rewriting sections with AI..."):

            summary_prompt = f"Write a Summary section for a {job_role} using the following resume:\n\n{resume_text}"
            projects_prompt = f"Rewrite the Projects section tailored for a {job_role}. Use LaTeX itemize format:\n\n{resume_text}"
            experience_prompt = f"Rewrite the Experience section tailored for a {job_role} using LaTeX bullet format:\n\n{resume_text}"
            education_prompt = f"Extract the Education section in LaTeX bullet format:\n\n{resume_text}"

            def ask_ai(prompt):
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192"
                )
                return response.choices[0].message.content.strip()

            summary = sanitize_latex(ask_ai(summary_prompt))
            projects = sanitize_latex(ask_ai(projects_prompt))
            experience = sanitize_latex(ask_ai(experience_prompt))
            education = sanitize_latex(ask_ai(education_prompt))

        with st.expander("🧠 AI-Rewritten Sections"):
            st.markdown(f"### 🧩 Summary\n{summary}")
            st.markdown(f"### 🛠 Projects\n{projects}")
            st.markdown(f"### 🏢 Experience\n{experience}")
            st.markdown(f"### 🎓 Education\n{education}")

        latex_code = build_resume_latex(summary, education, projects, experience)   
      with open("latex_output/error_debug.tex", "w", encoding="utf-8") as f:
    f.write(latex_code)
    st.warning("⚠️ LaTeX file saved as latex_output/error_debug.tex. Open this file in VS Code to fix LaTeX errors manually if needed.")
  st.text_area("📄 Final LaTeX Code", latex_code, height=400)

        final_pdf_path = generate_pdf_from_latex(latex_code, f"{job_role.replace(' ', '_')}_Resume")

        if final_pdf_path:
            with open(final_pdf_path, "rb") as f:
                st.download_button("📥 Download Final Resume PDF", f, file_name=os.path.basename(final_pdf_path))

    except Exception as e:
        st.error(f"❌ Error: {e}")
