import os
import tempfile
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq
import subprocess

# Load environment variables
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Configure Streamlit
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling + Animation
st.markdown("""
    <style>
    body {
        background-color: #1e1e2f;
        color: #ffffff;
    }
    .stApp {
        font-family: 'Segoe UI', sans-serif;
        animation: fadeIn 1.5s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .stButton > button {
        background-color: #0077ff;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    .stTextArea textarea {
        background-color: #2c2f4a;
        color: white;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Analyzer & Improver")
st.write("Upload your resume, select a job role, and get AI-powered feedback & an improved, LaTeX-formatted resume PDF.")

# Job roles
job_role = st.selectbox("Select Target Job Role", [
    "Web Developer",
    "Data Scientist",
    "UI/UX Designer",
    "Software Engineer",
    "Marketing Analyst"
])

# Upload PDF
uploaded_pdf = st.file_uploader("Upload Your Resume PDF", type=["pdf"])

if uploaded_pdf and job_role:
    try:
        # Extract resume text
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = ""
        for page in reader.pages:
            if page.extract_text():
                resume_text += page.extract_text()

        st.success("✅ Resume uploaded and text extracted.")

        with st.expander("🔍 View Extracted Resume Text"):
            st.text(resume_text)

        # Review prompt
        st.subheader("🧠 AI Review of Your Resume")
        review_prompt = f"""
You are an expert resume reviewer. Here is a resume:
\n{resume_text}\n
Give:
1. Problems or weaknesses
2. Suggestions to improve it
3. What's missing (e.g. summary, skills, projects)
4. Use simple language.
"""
        with st.spinner("Analyzing resume..."):
            review_response = client.chat.completions.create(
                messages=[{"role": "user", "content": review_prompt}],
                model="llama3-8b-8192"
            )
            review_feedback = review_response.choices[0].message.content.strip()
            with st.expander("💡 AI Suggestions"):
                st.markdown(review_feedback)

        # Improve resume prompt with LaTeX format
        st.subheader("🔧 Improved Resume Content (LaTeX)")
        improve_prompt = f'''
You are an expert resume writer and career consultant.

Rewrite the resume below into a highly tailored, professional resume for the job role of: {job_role}.

🛠️ Instructions:
- Highlight only the most relevant experience, skills, and projects for this job role.
- Use action verbs and achievement-oriented bullet points.
- Organize the resume in standard professional format (contact, summary, skills, experience, education, etc.).
- Use modern and polished language.
- Return output in clean LaTeX resume format using a minimal template.
- Do not explain the output, just return raw LaTeX content.

Original Resume:
{resume_text}
'''
        with st.spinner(f"Generating LaTeX resume for {job_role}..."):
            latex_response = client.chat.completions.create(
                messages=[{"role": "user", "content": improve_prompt}],
                model="llama3-8b-8192"
            )
            latex_code = latex_response.choices[0].message.content.strip()
            st.text_area("📄 Generated LaTeX Code", latex_code, height=400)

        # Save LaTeX code to .tex file and compile to PDF using pdflatex
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "resume.tex")
            with open(tex_path, "w", encoding="utf-8") as tex_file:
                tex_file.write(latex_code)

            try:
                subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_path], cwd=tmpdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pdf_path = os.path.join(tmpdir, "resume.pdf")
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download LaTeX Resume PDF", f, file_name=f"{job_role.replace(' ', '_')}_Resume_LaTeX.pdf")
            except Exception as compile_err:
                st.error("❌ LaTeX compilation failed. Ensure pdflatex is installed.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
