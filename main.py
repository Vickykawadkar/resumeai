import os
import re
import tempfile
import subprocess
from io import BytesIO
import streamlit as st
import PyPDF2
from dotenv import load_dotenv
from openai import OpenAI

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# UI setup
st.set_page_config(page_title="AI Resume Generator", page_icon="📄")
st.title("📄 AI Resume Generator")
st.write("Upload your resume → Select a job role → Get a clean, AI-enhanced 1-page resume.")

# File uploader and role selection
uploaded = st.file_uploader("📁 Upload Resume (PDF)", type=["pdf"])
roles = [
    "Software Developer", "Python Developer", "HR Manager", "Data Analyst",
    "Full Stack Developer", "Backend Developer", "Frontend Developer", "Java Developer"
]
role = st.selectbox("🎯 Select Target Job Role", ["-- Select --"] + roles)

# Extract text from PDF
resume_text = ""
if uploaded:
    reader = PyPDF2.PdfReader(BytesIO(uploaded.read()))
    for page in reader.pages:
        resume_text += page.extract_text() + "\n"
    resume_text = resume_text.strip()

# GPT Resume Generator
def get_resume_content(role, resume_text):
    prompt = f"""
You are an expert resume writer. Rewrite this resume for a '{role}' position.

Make it:
- Short (max 1 page)
- Clean and professional (black & white only)
- Use these sections: Summary, Core Skills, Experience, Projects, Education, Additional
- 3-5 lines per section, no filler.

Resume:
{resume_text}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # ✅ Updated to avoid GPT-4 error
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=1800
    )
    return response.choices[0].message.content

# LaTeX escape
def clean_latex(text):
    special = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}', '\\': r'\textbackslash{}'
    }
    for k, v in special.items():
        text = text.replace(k, v)
    return text

# Parse into sections
def parse_sections(gpt_text):
    sections = {'summary': '', 'skills': '', 'experience': '', 'projects': '', 'education': '', 'additional': ''}
    current = None
    for line in gpt_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        for key in sections:
            if key in line.lower():
                current = key
                break
        else:
            if current:
                sections[current] += line + ' '
    return {k: clean_latex(v.strip()) for k, v in sections.items()}

# LaTeX template
LATEX_TEMPLATE = r"""
\documentclass[10pt]{article}
\usepackage[margin=0.8in]{geometry}
\usepackage{titlesec, enumitem, parskip, xcolor, helvet}
\renewcommand{\familydefault}{\sfdefault}
\pagenumbering{gobble}
\titleformat{\section}{\bfseries\color{black}}{}{0em}{}
\titlespacing{\section}{0pt}{6pt}{4pt}

\begin{document}
\begin{center}
{\LARGE \textbf{AI Generated Resume}}\\
\textit{Target Role: \textbf{""" + role + r"""}}\\
\end{center}
\vspace{10pt}

\section*{Summary}
{summary}

\section*{Core Skills}
{skills}

\section*{Experience}
{experience}

\section*{Projects}
{projects}

\section*{Education}
{education}

\section*{Additional}
{additional}

\end{document}
"""

# Create PDF
def generate_pdf(latex_code, filename="Resume"):
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = os.path.join(tmp, filename + ".tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        try:
            for _ in range(2):
                subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_path],
                               cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pdf_path = os.path.join(tmp, filename + ".pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
        except Exception as e:
            st.error("LaTeX error: " + str(e))
    return None

# Action Button
if st.button("🚀 Generate Resume"):
    if not resume_text:
        st.error("❌ Please upload your resume.")
    elif role == "-- Select --":
        st.error("❌ Please select a job role.")
    else:
        with st.spinner("🤖 GPT is rewriting your resume..."):
            gpt_output = get_resume_content(role, resume_text)
            sections = parse_sections(gpt_output)
            latex = LATEX_TEMPLATE.format(**sections)
            pdf = generate_pdf(latex, "AI_Resume")
            if pdf:
                st.success("✅ Resume ready!")
                st.download_button("📥 Download Resume", data=pdf,
                                   file_name=f"Resume_{role.replace(' ', '_')}.pdf",
                                   mime="application/pdf")
            else:
                st.error("❌ PDF generation failed.")
