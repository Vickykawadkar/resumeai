import os
import tempfile
import re
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from openai import OpenAI

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# Sanitize LaTeX text
def sanitize_latex(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", text)
    replacements = {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"
    }
    for key, val in replacements.items():
        text = text.replace(key, val)
    text = re.sub(r"(Note:|Let me know.*|This summary.*|In this rewritten.*)", "", text, flags=re.IGNORECASE)
    return text.strip()

# Read template
TEMPLATE_PATH = "resume_template.tex"
def load_template():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

def generate_latex(template: str, replacements: dict) -> str:
    for key, val in replacements.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template

# Compile PDF
def generate_pdf_from_latex(latex_code: str, filename: str):
    with tempfile.TemporaryDirectory() as tmpdirname:
        tex_path = os.path.join(tmpdirname, f"{filename}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        os.system(f"pdflatex -output-directory={tmpdirname} {tex_path} > /dev/null 2>&1")
        pdf_path = os.path.join(tmpdirname, f"{filename}.pdf")
        if os.path.exists(pdf_path):
            return pdf_path
    return None

# Main Flow
if uploaded_pdf and job_role:
    try:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = "".join([p.extract_text() or "" for p in reader.pages])
        st.success("✅ Resume uploaded and text extracted.")
        with st.expander("🔍 View Extracted Resume Text"):
            st.text(resume_text)

        with st.spinner("🔍 Extracting and rewriting sections with AI..."):
            def ask_ai(prompt):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()

            summary = sanitize_latex(ask_ai(f"Write a Summary section for a {job_role} using the following resume:\n\n{resume_text}"))
            projects = sanitize_latex(ask_ai(f"Rewrite the Projects section tailored for a {job_role}. Use LaTeX itemize format:\n\n{resume_text}"))
            experience = sanitize_latex(ask_ai(f"Rewrite the Experience section tailored for a {job_role} using LaTeX bullet format:\n\n{resume_text}"))
            education = sanitize_latex(ask_ai(f"Extract the Education section in LaTeX bullet format:\n\n{resume_text}"))

        with st.expander("🧠 AI-Rewritten Sections"):
            st.markdown(f"### 🧩 Summary\n{summary}")
            st.markdown(f"### 🛠 Projects\n{projects}")
            st.markdown(f"### 🏢 Experience\n{experience}")
            st.markdown(f"### 🎓 Education\n{education}")

        # Dynamic LaTeX Fill
        latex_template = load_template()
        latex_code = generate_latex(latex_template, {
            "SUMMARY": summary,
            "PROJECTS": projects,
            "EXPERIENCE": experience,
            "EDUCATION": education,
        })

        st.text_area("📄 Final LaTeX Code", latex_code, height=400)

        final_pdf_path = generate_pdf_from_latex(latex_code, f"{job_role.replace(' ', '_')}_Resume")
        if final_pdf_path:
            with open(final_pdf_path, "rb") as f:
                st.download_button("📥 Download Final Resume PDF", f, file_name=os.path.basename(final_pdf_path))

    except Exception as e:
        st.error(f"❌ Error: {e}")
