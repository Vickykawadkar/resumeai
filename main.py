import os
import tempfile
import re
import subprocess
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
from groq import Groq

# Load API key from .env file
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")
    st.stop()

client = Groq(api_key=groq_api_key)

# Streamlit setup
st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="centered")

# Custom CSS for styling the Streamlit app
st.markdown("""
<style>
body { background-color: #0f172a; color: #f1f5f9; }
.stApp { font-family: 'Segoe UI', sans-serif; }
.stButton > button {
    background-color: #0ea5e9;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    border: none;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
.stButton > button:hover {
    background-color: #0284c7;
}
.stTextArea textarea, .stTextInput input {
    background-color: #1e293b;
    color: #f8fafc;
    border-radius: 10px;
    border: 1px solid #334155;
    padding: 10px;
}
.streamlit-expanderHeader {
    background-color: #334155;
    color: #f1f5f9;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
.streamlit-expanderContent {
    background-color: #1e293b;
    border-radius: 0 0 8px 8px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("📄 AI Resume Optimizer (LaTeX PDF)")
st.write("Upload your resume, select a target job role, and get a LaTeX-formatted PDF with optimized content.")

job_role = st.selectbox("🎯 Target Job Role", [
    "Web Developer", "Data Scientist", "UI/UX Designer", "Software Engineer",
    "Marketing Analyst", "Product Manager", "Business Analyst",
    "Cybersecurity Analyst", "DevOps Engineer", "AI/ML Engineer"
])

uploaded_pdf = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"])

def sanitize_latex(text: str) -> str:
    """
    Escapes special characters in a string to make it safe for LaTeX.
    Also converts Markdown bold/italic to LaTeX equivalents.
    """
    if not text:
        return ""
    
    # Convert Markdown bold (**) and italic (*) to LaTeX \textbf{} and \textit{}
    text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"\*(.*?)\*", r"\\textit{\1}", text)

    # Define LaTeX special characters and their escaped versions
    # IMPORTANT: Backslash must be escaped first to avoid double-escaping issues
    ordered_replacements = [
        ("\\", "\\textbackslash{}"), # Escape backslash itself first
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
        ("<", "\\textless{}"),
        (">", "\\textgreater{}"),
    ]
    
    for k, v in ordered_replacements:
        text = text.replace(k, v)
        
    return text.strip()

def extract_contact_info(text: str) -> dict:
    """
    Extracts name, email, phone, and LinkedIn from the extracted resume text.
    """
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[^\s]+", text)
    
    name = ""
    for line in text.split('\n'):
        stripped_line = line.strip()
        if stripped_line and not any(char.isdigit() or '@' in char or 'linkedin.com' in char for char in stripped_line):
            name = stripped_line
            break
    
    return {
        "NAME": sanitize_latex(name),
        "EMAIL": email.group(0) if email else "",
        "PHONE": phone.group(0) if phone else "",
        "LINKEDIN": linkedin.group(0) if linkedin else "",
        "LOCATION": "India" 
    }

def load_template_string() -> str:
    """
    Returns the LaTeX resume template as a multi-line string, based on the user's provided .tex file.
    Modified for 1-page compactness and to remove parskip.
    """
    return r"""
\documentclass[10pt]{article} % Changed to 10pt for compactness
\usepackage[margin=0.5in]{geometry} % Further reduced margins for more space
\usepackage[hidelinks]{hyperref}
\usepackage{enumitem}
% \usepackage{parskip} % Removed parskip for tighter spacing
\usepackage[T1]{fontenc}
\renewcommand{\familydefault}{\sfdefault}
\pagenumbering{gobble}

% Adjust spacing parameters
\setlength{\parskip}{0pt} % No space between paragraphs
\setlength{\parsep}{0pt}  % No space between items in lists
\setlength{\itemsep}{0pt} % No space between list items
\setlength{\topsep}{0pt}  % No space above/below lists

\begin{document}

\noindent
\textbf{\LARGE {{{NAME}}}} \\[-6pt] % Further reduced line spacing here
{{{LOCATION}}} \textbullet{} {{{PHONE}}} \textbullet{} \href{{mailto:{{{EMAIL}}}}}{{{EMAIL}}} \\[-6pt] % Further reduced line spacing here
\href{{{{{LINKEDIN}}}}}{{{LINKEDIN}}}

% Reduced vertical space after section titles for compactness
\section*{Summary}
\vspace{-0.25in} % Even more aggressive reduction
{{{SUMMARY}}}

\section*{Skills}
\vspace{-0.25in} % Even more aggressive reduction
{{{SKILLS}}}

\section*{Work Experience}
\vspace{-0.25in} % Even more aggressive reduction
{{{EXPERIENCE}}}

\section*{Projects}
\vspace{-0.25in} % Even more aggressive reduction
{{{PROJECTS}}}

\section*{Education}
\vspace{-0.25in} % Even more aggressive reduction
{{{EDUCATION}}}

\end{document}
"""

def fill_template(template: str, values: dict) -> str:
    """
    Replaces placeholders in the LaTeX template with actual content.
    """
    for k, v in values.items():
        template = template.replace(f"{{{{{k}}}}}", v or "")
    return template

def generate_pdf(latex_code: str, filename: str) -> tuple[bytes | None, str | None]:
    """
    Generates a PDF from LaTeX code using pdflatex.
    Returns a tuple: (PDF bytes if successful, LaTeX error log string if failed).
    If successful, error log is None. If failed, PDF bytes is None.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, f"{filename}.tex")
        pdf_file = os.path.join(tmpdir, f"{filename}.pdf")
        
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_code)

        st.info(f"Attempting to compile LaTeX to PDF in: {tmpdir}")
        
        try:
            # Run pdflatex twice for correct cross-referencing and layout stability
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={tmpdir}", tex_file],
                capture_output=True, text=True, check=False
            )
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"-output-directory={tmpdir}", tex_file],
                capture_output=True, text=True, check=False
            )
            log_content = result.stdout + result.stderr

            if os.path.exists(pdf_file):
                st.success("PDF generated successfully!")
                with open(pdf_file, "rb") as f:
                    pdf_bytes = f.read()
                return pdf_bytes, None
            else:
                st.error("PDF generation failed. Checking log for errors...")
                return None, log_content[-3000:] if len(log_content) > 3000 else log_content
        except FileNotFoundError:
            return None, "Error: 'pdflatex' command not found. Please ensure LaTeX is installed and in your system's PATH."
        except Exception as e:
            return None, f"An unexpected error occurred during pdflatex execution: {e}"

def ask_ai(prompt: str) -> str:
    """
    Sends a prompt to the Groq AI model and returns the response.
    """
    res = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return res.choices[0].message.content.strip()

if uploaded_pdf and job_role:
    try:
        reader = PyPDF2.PdfReader(uploaded_pdf)
        resume_text = "".join([p.extract_text() or "" for p in reader.pages])
        
        user_info = extract_contact_info(resume_text)

        st.success("✅ Resume uploaded and text extracted.")
        with st.expander("📄 View Extracted Text"):
            st.text(resume_text)
        
        with st.spinner("🤖 Rewriting resume sections with AI..."):
            # Prompt for Summary: extremely concise, plain text
            summary_prompt = (
                f"Based on the following resume text, write a professional Summary section "
                f"for a {job_role} resume. Keep it to the absolute bare minimum words (max 1-2 lines, 30-50 words) and impactful. "
                f"Absolutely no LaTeX commands or bullet points. "
                f"This section MUST be extremely short to fit on a single page with absolutely minimal spacing. "
                f"Prioritize fitting on a single page above all else. "
                f"Resume text:\n{resume_text}"
            )
            summary = sanitize_latex(ask_ai(summary_prompt))

            # Prompt for Skills: concise, LaTeX itemize
            skills_prompt = (
                f"Based on the following resume text, extract and rewrite the most relevant Skills "
                f"for a {job_role} role. Prioritize the most critical and relevant skills (top 3-5 categories with 2-4 skills each). "
                f"Categorize them (e.g., Programming Languages, Web Technologies, Databases, Tools & Platforms, Other). "
                f"Format it strictly using LaTeX `\\begin{{itemize}}` and `\\item` commands for bullet points. "
                f"Each category should be `\\item \\textbf{{Category Name}}: Skill1, Skill2, Skill3.` "
                f"Keep the total length of the section extremely short to fit on one page with absolutely minimal spacing. "
                f"Ensure all special LaTeX characters are properly escaped. Prioritize fitting on a single page above all else. "
                f"Resume text:\n{resume_text}"
            )
            skills = ask_ai(skills_prompt)

            # Prompt for Experience: concise, LaTeX itemize
            experience_prompt = (
                f"Based on the following resume text, rewrite the Experience section for a {job_role} resume. "
                f"Focus on achievements and responsibilities relevant to the {job_role} role. "
                f"Limit to your most recent and impactful 1-2 roles. " # Limit number of roles
                f"For each role, provide only 1-2 extremely concise, achievement-oriented, keyword-rich bullet points. " # Limit bullet points per role
                f"Format it strictly using LaTeX `\\begin{{itemize}}` and `\\item` commands for bullet points. "
                f"Each job entry should start with `\\item \\textbf{{Job Title}} at \\textbf{{Company Name}}, Location (Dates).` "
                f"The entire experience section MUST be extremely brief to fit on one page with absolutely minimal spacing. "
                f"Ensure all special LaTeX characters are properly escaped. Prioritize fitting on a single page above all else. "
                f"Resume text:\n{resume_text}"
            )
            experience = ask_ai(experience_prompt)

            # Prompt for Projects: concise, LaTeX itemize
            projects_prompt = (
                f"Based on the following resume text, rewrite the Projects section for a {job_role} resume. "
                f"Highlight your top 1-2 most impactful projects relevant to the {job_role} role. " # Limit number of projects
                f"For each project, provide only 1-2 extremely concise, keyword-rich bullet points focusing on impact and technologies used. " # Limit bullet points per project
                f"Format it strictly using LaTeX `\\begin{{itemize}}` and `\\item` commands for bullet points. "
                f"Each project should start with `\\item \\textbf{{Project Name}}: Description.` "
                f"The entire projects section MUST be extremely brief to fit on one page with absolutely minimal spacing. "
                f"Ensure all special LaTeX characters are properly escaped. Prioritize fitting on a single page above all else. "
                f"Resume text:\n{resume_text}"
            )
            projects = ask_ai(projects_prompt)

            # Prompt for Education: concise, LaTeX itemize
            education_prompt = (
                f"Based on the following resume text, extract and rewrite the Education section. "
                f"Keep it extremely concise (1-2 entries max if possible). " # Limit number of education entries
                f"Format it strictly using LaTeX `\\begin{{itemize}}` and `\\item` commands for bullet points. "
                f"Each education entry should start with `\\item \\textbf{{Degree, Major}}, University Name, Location (Graduation Date).` "
                f"The entire education section MUST be extremely brief to fit on one page with absolutely minimal spacing. "
                f"Ensure all special LaTeX characters are properly escaped. Prioritize fitting on a single page above all else. "
                f"Resume text:\n{resume_text}"
            )
            education = ask_ai(education_prompt)

        st.success("🤖 AI rewriting complete!")
        with st.expander("🧑‍🧐 View Rewritten Sections (AI Output)"):
            st.markdown(f"**Summary**\n\n{summary}")
            st.markdown(f"**Skills**\n\n```latex\n{skills}\n```")
            st.markdown(f"**Experience**\n\n```latex\n{experience}\n```")
            st.markdown(f"**Projects**\n\n```latex\n{projects}\n```")
            st.markdown(f"**Education**\n\n```latex\n{education}\n```")

        template = load_template_string()
        latex_code = fill_template(template, {
            **user_info,
            "SUMMARY": summary,
            "SKILLS": skills,
            "PROJECTS": projects,
            "EXPERIENCE": experience,
            "EDUCATION": education,
        })

        st.text_area("📄 Final LaTeX Code (for review)", latex_code, height=400)

        safe_name = job_role.replace(" ", "_").replace("/", "-")
        pdf_bytes, error_log = generate_pdf(latex_code, f"{safe_name}_Resume")

        if pdf_bytes:
            st.download_button(
                "⬇️ Download Optimized Resume PDF",
                pdf_bytes,
                file_name=f"{safe_name}_Optimized_Resume.pdf",
                mime="application/pdf"
            )
        else:
            st.error("❌ PDF generation failed. Please review the LaTeX error log below.")
            if error_log:
                st.text_area("📜 LaTeX Error Log", error_log, height=300)
            
            debug_tex_path = os.path.join(tempfile.gettempdir(), "generated_resume_debug.tex")
            with open(debug_tex_path, "w", encoding="utf-8") as f:
                f.write(latex_code)
            with open(debug_tex_path, "rb") as f:
                st.download_button("⬇️ Download LaTeX Code (.tex) for Debugging", f, file_name="resume_debug.tex")

    except PyPDF2.errors.PdfReadError:
        st.error("❌ Failed to read the PDF file. It might be corrupted or password-protected.")
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {e}")
        st.exception(e)
