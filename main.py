import os
import tempfile
import re
import subprocess
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq

# Load API key
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found. Please set it in your .env file.")
    st.stop()

client = Groq(api_key=groq_api_key)

st.set_page_config(page_title="AI Resume Optimizer", page_icon="📄", layout="centered")
st.title("📄 AI Resume Optimizer (Professional 1-Page PDF)")
st.write("Upload your resume, select a job role, and get a **1-page optimized PDF** in professional format (blue headers, proper spacing, modern font).")

# --- Styling for Streamlit ---
st.markdown("""
<style>
body { background-color: #0f172a; color: #f1f5f9; }
.stApp { font-family: 'Segoe UI', sans-serif; }
.stButton > button {
    background-color: #0ea5e9; color: white; border-radius: 8px;
    padding: 10px 20px; font-weight: bold; border: none;
}
.stButton > button:hover { background-color: #0284c7; }
.stTextArea textarea, .stTextInput input {
    background-color: #1e293b; color: #f8fafc; border-radius: 10px;
    border: 1px solid #334155; padding: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- Job Roles ---
job_role = st.selectbox("🎯 Target Job Role", [
    "Web Developer", "Data Scientist", "UI/UX Designer", "Software Engineer",
    "Marketing Analyst", "Product Manager", "Business Analyst",
    "Cybersecurity Analyst", "DevOps Engineer", "AI/ML Engineer"
])

uploaded_pdf = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

# --- Helper Functions ---
def sanitize_latex(text: str) -> str:
    """Escape LaTeX special chars + convert markdown."""
    if not text: return ""
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", text)
    for k, v in [
        ("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"),
        ("$", "\\$"), ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"),
        ("~", "\\textasciitilde{}"), ("^", "\\textasciicircum{}"),
        ("<", "\\textless{}"), (">", "\\textgreater{}"),
    ]:
        text = text.replace(k, v)
    return text.strip()

def extract_contact_info(text: str) -> dict:
    """Extract name, email, phone, LinkedIn from resume text."""
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[^\s]+", text)
    name = ""
    for line in text.splitlines():
        if line.strip() and not any(c.isdigit() or '@' in c or 'linkedin.com' in c for c in line):
            name = line.strip(); break
    return {
        "NAME": sanitize_latex(name),
        "EMAIL": email.group(0) if email else "",
        "PHONE": phone.group(0) if phone else "",
        "LINKEDIN": linkedin.group(0) if linkedin else "",
        "LOCATION": "India"
    }

def load_template() -> str:
    """LaTeX template with professional styling (blue headers, proper spacing)."""
    return r"""
\documentclass[10pt]{article}
\usepackage[margin=0.6in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\renewcommand{\familydefault}{\sfdefault}
\pagenumbering{gobble}

% Colors
\definecolor{sectionblue}{HTML}{1E90FF}
\definecolor{textgray}{HTML}{222222}

% Compact spacing
\setlength{\parskip}{4pt}
\setlength{\parsep}{0pt}
\setlength{\itemsep}{4pt}
\setlength{\topsep}{4pt}

\begin{document}
\color{textgray}
\noindent
{\LARGE \textbf{{{NAME}}}} \\[2pt]
{{{LOCATION}}} • {{{PHONE}}} • \href{{mailto:{{{EMAIL}}}}}{{{EMAIL}}} \\[2pt]
\href{{{{{LINKEDIN}}}}}{{{LINKEDIN}}}

\vspace{4pt}
\textcolor{sectionblue}{\rule{\linewidth}{0.8pt}}

\section*{\textcolor{sectionblue}{Summary}}
{{{SUMMARY}}}

\section*{\textcolor{sectionblue}{Skills}}
{{{SKILLS}}}

\section*{\textcolor{sectionblue}{Work Experience}}
{{{EXPERIENCE}}}

\section*{\textcolor{sectionblue}{Projects}}
{{{PROJECTS}}}

\section*{\textcolor{sectionblue}{Education}}
{{{EDUCATION}}}
\end{document}
"""

def fill_template(template: str, values: dict) -> str:
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", v or "")
    return template

def generate_pdf(latex_code: str, filename: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, f"{filename}.tex")
        pdf_file = os.path.join(tmpdir, f"{filename}.pdf")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_code)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", f"-output-directory={tmpdir}", tex_file],
            capture_output=True, text=True
        )
        if os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                return f.read(), None
        return None, result.stdout + result.stderr

def ask_ai(prompt: str) -> str:
    res = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    return res.choices[0].message.content.strip()

def ai_section(prompt):
    strict_prompt = f"""
{prompt}

IMPORTANT:
1. Output ONLY valid LaTeX.
2. Start with \\begin{{itemize}} and end with \\end{{itemize}}.
3. Maximum 3-4 bullet points (keep concise, each <= 15 words).
4. No extra text or headings outside the list.
5. Escape all LaTeX special characters.
"""
    return sanitize_latex(ask_ai(strict_prompt))

# --- Main Logic ---
if uploaded_pdf and job_role:
    try:
        text = "".join([p.extract_text() or "" for p in PyPDF2.PdfReader(uploaded_pdf).pages])
        user_info = extract_contact_info(text)
        st.success("✅ Resume uploaded and extracted!")

        with st.spinner("🤖 Optimizing resume..."):
            summary = sanitize_latex(ask_ai(f"Make a 1-2 line impactful summary for a {job_role} resume:\n{text}"))
            skills = ai_section(f"Extract top categorized skills for {job_role} from:\n{text}")
            experience = ai_section(f"Summarize 1-2 most recent roles (max 2 bullets each) for {job_role}:\n{text}")
            projects = ai_section(f"Highlight 1-2 key projects (1 bullet each) for {job_role}:\n{text}")
            education = ai_section(f"Extract 1-2 education entries (concise) from:\n{text}")

        latex_code = fill_template(load_template(), {
            **user_info,
            "SUMMARY": summary,
            "SKILLS": skills,
            "EXPERIENCE": experience,
            "PROJECTS": projects,
            "EDUCATION": education
        })

        pdf_bytes, log = generate_pdf(latex_code, job_role.replace(" ", "_"))
        if pdf_bytes:
            st.download_button("⬇️ Download Optimized Resume", pdf_bytes,
                               file_name=f"{job_role}_Resume.pdf", mime="application/pdf")
        else:
            st.error("❌ PDF generation failed. Check the LaTeX error log below.")
            st.text_area("Error Log", log, height=300)
    except Exception as e:
        st.error(f"Error: {e}")
