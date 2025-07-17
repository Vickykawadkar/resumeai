import os
import tempfile
import re
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq

# Load API key from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Streamlit setup
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="centered")

# Styles
st.markdown("""
<style>
body { background-color: #0f172a; color: #f1f5f9; }
.stApp { font-family: 'Segoe UI', sans-serif; }
.stButton > button { background-color: #0ea5e9; color: white; border-radius: 8px; padding: 10px 20px; font-weight: bold; }
.stButton > button:hover { background-color: #0284c7; }
.stTextArea textarea { background-color: #1e293b; color: #f8fafc; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Optimizer (LaTeX PDF)")
st.write("Upload resume, select a role, and download LaTeX-formatted PDF with optimized content.")

job_role = st.selectbox("🎯 Target Job Role", [
    "Web Developer", "Data Scientist", "UI/UX Designer", "Software Engineer",
    "Marketing Analyst", "Product Manager", "Business Analyst",
    "Cybersecurity Analyst", "DevOps Engineer", "AI/ML Engineer"
])

uploaded_pdf = st.file_uploader("📤 Upload Resume (PDF)", type=["pdf"])

# Basic LaTeX cleanup

def sanitize_latex(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", text)
    replacements = {
        "&": "\\&", "%": "\\%", "$": "\\$", "#": "\\#",
        "_": "\\_", "{": "\\{", "}": "\\}", "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}", "\\": "\\textbackslash{}"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.strip()

# Fix Groq LaTeX escaping

def fix_ai_format(text: str) -> str:
    return text.replace("\\textbackslash{}", "\\").replace("•", "-").strip()

# Extract name/email/phone/linkedin

def extract_contact_info(text):
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+", text)
    phone = re.search(r"\\+?\\d[\\d\\s\\-]{9,}", text)
    linkedin = re.search(r"(https?:\\/\\/)?(www\\.)?linkedin\\.com\\/[^\\s]+", text)
    name = text.split('\n')[0] if text else ""
    return {
        "NAME": name.strip(),
        "EMAIL": email.group(0) if email else "",
        "PHONE": phone.group(0) if phone else "",
        "LINKEDIN": linkedin.group(0) if linkedin else "",
        "LOCATION": "India"  # default fallback
    }

# Template tools

def load_template():
    with open("resume_template.tex", "r", encoding="utf-8") as f:
        return f.read()

def fill_template(template, values):
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template

# LaTeX to PDF

def generate_pdf(latex_code, filename):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, f"{filename}.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_code)
        os.system(f"pdflatex -output-directory={tmpdir} {tex_file} > /dev/null 2>&1")
        pdf_file = os.path.join(tmpdir, f"{filename}.pdf")
        return pdf_file if os.path.exists(pdf_file) else None

# Ask AI

def ask_ai(prompt):
    res = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

# Main logic
if uploaded_pdf and job_role:
    try:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = "".join([p.extract_text() or "" for p in reader.pages])
        user_info = extract_contact_info(resume_text)

        st.success("✅ Resume uploaded and text extracted.")
        with st.expander("📄 View Extracted Text"):
            st.text(resume_text)

        with st.spinner("🤖 Rewriting with AI..."):
            summary = sanitize_latex(ask_ai(f"Write a professional Summary section for a {job_role} resume:\n{resume_text}"))
            projects = fix_ai_format(ask_ai(f"Rewrite the Projects section for a {job_role} in LaTeX itemize format:\n{resume_text}"))
            experience = fix_ai_format(ask_ai(f"Rewrite the Experience section in LaTeX bullet format:\n{resume_text}"))
            education = fix_ai_format(ask_ai(f"Extract the Education section in LaTeX bullet format:\n{resume_text}"))

        with st.expander("🧠 Rewritten Sections"):
            st.markdown(f"**Summary**\n\n{summary}")
            st.markdown(f"**Projects**\n\n{projects}")
            st.markdown(f"**Experience**\n\n{experience}")
            st.markdown(f"**Education**\n\n{education}")

        # Final render
        template = load_template()
        latex_code = fill_template(template, {
            **user_info,
            "SUMMARY": summary,
            "PROJECTS": projects,
            "EXPERIENCE": experience,
            "EDUCATION": education
        })

        with open("generated_resume_debug.tex", "w", encoding="utf-8") as f:
            f.write(latex_code)
        st.text_area("📄 Final LaTeX Code", latex_code, height=400)

        safe_name = job_role.replace(" ", "_").replace("/", "-")
        pdf_path = generate_pdf(latex_code, f"{safe_name}_Resume")

        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download Final Resume PDF", f, file_name=os.path.basename(pdf_path))
        else:
            st.error("❌ PDF generation failed. Check LaTeX syntax in sections.")

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")