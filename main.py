import os
import tempfile
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq
from fpdf import FPDF

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

# Custom Styling + Animation (Updated Theme)
st.markdown("""
    <style>
    body {
        background-color: #0f172a;
        color: #f1f5f9;
    }
    .stApp {
        font-family: 'Segoe UI', sans-serif;
        animation: fadeIn 1s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(-10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .stButton > button {
        background-color: #0ea5e9;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.2s ease-in-out;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0284c7;
    }
    .stTextArea textarea {
        background-color: #1e293b;
        color: #f8fafc;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Analyzer & Improver")
st.write("Upload your resume, select a job role, and get an AI-upgraded version with personalized content and preserved formatting.")

job_role = st.selectbox("Select Target Job Role", [
    "Web Developer",
    "Data Scientist",
    "UI/UX Designer",
    "Software Engineer",
    "Marketing Analyst",
    "Product Manager",
    "Business Analyst",
    "Cybersecurity Analyst",
    "DevOps Engineer",
    "AI/ML Engineer"
])

uploaded_pdf = st.file_uploader("Upload Your Resume PDF", type=["pdf"])

if uploaded_pdf and job_role:
    try:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = ""
        for page in reader.pages:
            if page.extract_text():
                resume_text += page.extract_text()

        st.success("✅ Resume uploaded and text extracted.")
        with st.expander("🔍 View Extracted Resume Text"):
            st.text(resume_text)

        # Resume review
        st.subheader("🧠 AI Resume Feedback")
        review_prompt = f"""
You are a professional resume reviewer.
Analyze the resume below and identify:
- Weak points
- Sections to improve
- Missing elements for the selected job role: {job_role}
Use clear, simple suggestions without altering the original format.

Resume:
{resume_text}
"""
        with st.spinner("Analyzing resume..."):
            review_response = client.chat.completions.create(
                messages=[{"role": "user", "content": review_prompt}],
                model="llama3-8b-8192"
            )
            review_feedback = review_response.choices[0].message.content.strip()
            with st.expander("💡 AI Suggestions"):
                st.markdown(review_feedback)

        # Resume rewriting prompt
        st.subheader("📄 Role-Specific Resume Content")
        improve_prompt = f'''
You are a resume optimization expert.

Improve the following resume text specifically for the role of {job_role}, without changing the original structure, font style, or layout. Only update:
- Summary
- Keywords
- Wording of bullets
- Job-specific relevance

Keep headings, font style, formatting, and section order exactly as provided.
Only modify content inside sections so the resume remains natural and looks human-written.
Do not add any AI-markers or extra sections.

Resume:
{resume_text}
'''
        with st.spinner(f"Improving resume content for {job_role}..."):
            improved_response = client.chat.completions.create(
                messages=[{"role": "user", "content": improve_prompt}],
                model="llama3-8b-8192"
            )
            improved_text = improved_response.choices[0].message.content.strip()
            st.text_area("📄 Improved Resume Text", improved_text, height=400)

        # Generate PDF using fpdf with fixed formatting
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=11)

        for line in improved_text.split("\n"):
            clean_line = line.replace("•", "-").encode("latin-1", errors="replace").decode("latin-1")
            if clean_line.strip() == "":
                pdf.ln(4)
            elif any(clean_line.lower().startswith(section) for section in ["summary", "skills", "experience", "education", "projects"]):
                pdf.set_font("Times", 'B', 12)
                pdf.multi_cell(0, 8, clean_line.strip())
                pdf.set_font("Times", '', 11)
            else:
                pdf.multi_cell(0, 8, clean_line.strip())

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_pdf.name)

        with open(temp_pdf.name, "rb") as f:
            st.download_button("📥 Download Final Resume PDF", f, file_name=f"{job_role.replace(' ', '_')}_Resume.pdf")

    except Exception as e:
        st.error(f"❌ Error: {e}")