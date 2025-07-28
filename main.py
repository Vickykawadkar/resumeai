import os
import tempfile
import re
import subprocess
from dotenv import load_dotenv
import streamlit as st
from groq import Groq
import PyPDF2
from io import BytesIO

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Page config
st.set_page_config(
    page_title="Resume Builder",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Professional Resume Builder")
st.write("PDF upload karo → Job role select karo → Clean PDF download karo!")

# PDF Upload Section
st.markdown("### 📁 Resume PDF Upload Karo:")
uploaded_file = st.file_uploader(
    "Choose PDF file",
    type=['pdf'],
    help="Resume PDF upload karo"
)

resume_text = ""

if uploaded_file is not None:
    try:
        # Read PDF
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
        resume_text = ""
        for page in pdf_reader.pages:
            resume_text += page.extract_text() + "\n"
        
        if resume_text.strip():
            st.success("✅ PDF successfully read!")
            with st.expander("Original Resume Preview"):
                st.text(resume_text[:400] + "...")
        else:
            st.error("❌ PDF se text extract nahi hua")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Job Role Selection
st.markdown("### 🎯 Target Job Role Select Karo:")

job_roles = [
    "Software Developer",
    "Data Scientist", 
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "UI/UX Designer",
    "Data Analyst",
    "Product Manager",
    "Digital Marketing Specialist",
    "Business Analyst",
    "DevOps Engineer",
    "Machine Learning Engineer",
    "Content Writer",
    "Python Developer",
    "Java Developer",
    "React Developer"
]

selected_role = st.selectbox("Job role choose karo:", ["Select role..."] + job_roles)

if selected_role != "Select role...":
    st.success(f"✅ Target Role: **{selected_role}**")

# Professional LaTeX Template
LATEX_TEMPLATE = r"""
\documentclass[letterpaper,11pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage{{parskip}}
\usepackage[margin=0.8in]{{geometry}}
\usepackage{{titlesec}}
\usepackage{{enumitem}}
\usepackage{{helvet}}
\usepackage{{xcolor}}
\renewcommand{{\familydefault}}{{\sfdefault}}
\pagenumbering{{gobble}}

% Professional section formatting
\titleformat{{\section}}{{\large\bfseries\color{{black}}}}{{}}{{0em}}{{}}[\color{{black}}{{\titlerule[1pt]}}]
\titlespacing*{{\section}}{{0pt}}{{10pt}}{{6pt}}
\setlist[itemize]{{leftmargin=15pt,itemsep=3pt,parsep=0pt,topsep=3pt}}

\begin{{document}}

% Header
\begin{{center}}
    {{\LARGE \textbf{{\color{{black}}{{{name}}}}}}} \\[4pt]
    {{\color{{black}}{{{contact}}}}} \\[10pt]
\end{{center}}

\section*{{\color{{black}}{{Professional Summary}}}}
\color{{black}}{{{summary}}}

\section*{{\color{{black}}{{Core Skills}}}}
\color{{black}}{{{skills}}}

\section*{{\color{{black}}{{Professional Experience}}}}
\color{{black}}{{{experience}}}

\section*{{\color{{black}}{{Key Projects}}}}
\color{{black}}{{{projects}}}

\section*{{\color{{black}}{{Education}}}}
\color{{black}}{{{education}}}

\end{{document}}
"""

def extract_personal_info(text):
    """Extract name and contact with better parsing"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    name = "Your Name"
    contact_parts = []
    
    # Find name (first meaningful line)
    for line in lines[:3]:
        if len(line.split()) <= 4 and not any(char in line for char in ['@', '+', '(', ')', 'phone', 'email', 'www']):
            # Clean name
            name = re.sub(r'[^\w\s]', '', line).strip()
            if name:
                break
    
    # Extract contact information
    for line in lines[:10]:
        # Email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
        if email_match:
            contact_parts.append(email_match.group())
        
        # Phone
        phone_match = re.search(r'[\+]?[0-9]{10,15}', line)
        if phone_match and phone_match.group() not in [part for part in contact_parts]:
            contact_parts.append(phone_match.group())
        
        # Location (Indian cities)
        cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'hyderabad', 'kolkata', 'indore', 'ahmedabad', 'jaipur']
        for city in cities:
            if city in line.lower() and line not in contact_parts:
                contact_parts.append(line.strip())
                break
    
    # Format contact info
    contact_info = " | ".join(contact_parts[:3]) if contact_parts else "Contact Information"
    
    return name, contact_info

def clean_content(text):
    """Remove unwanted characters and symbols"""
    if not text:
        return ""
    
    # Remove various unwanted symbols
    text = re.sub(r'[*]{2,}', '', text)  # Remove ** 
    text = re.sub(r'[+]{2,}', '', text)  # Remove ++
    text = re.sub(r'[\[\]{}()]', '', text)  # Remove brackets
    text = re.sub(r'[-]{2,}', '-', text)  # Multiple dashes to single
    text = re.sub(r'[|]{2,}', '|', text)  # Multiple pipes to single
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    
    # Clean LaTeX special characters
    latex_chars = {
        '&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#',
        '_': '\\_', '^': '\\textasciicircum{}', '~': '\\textasciitilde{}'
    }
    
    for char, replacement in latex_chars.items():
        text = text.replace(char, replacement)
    
    return text.strip()

def format_as_bullets(content, max_points=6):
    """Convert content to clean bullet points"""
    if not content or content.strip() == "":
        return "Information not available"
    
    # Clean content first
    content = clean_content(content)
    
    # Split into lines and filter
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    if not lines:
        return "Information not available"
    
    # Create clean bullet points
    bullets = []
    for line in lines[:max_points]:
        if len(line) > 5:  # Only meaningful content
            # Remove existing bullet symbols
            line = re.sub(r'^[-•*+]\s*', '', line)
            if line:
                bullets.append(f"\\item {line}")
    
    if bullets:
        return "\\begin{itemize}\n" + "\n".join(bullets) + "\n\\end{itemize}"
    else:
        return "Information not available"

def generate_professional_resume(original_resume, target_role):
    """Generate clean, professional resume content"""
    
    professional_prompt = f"""
You are a professional resume writer. Transform the following resume for a {target_role} position.

IMPORTANT REQUIREMENTS:
1. Write in clean, professional language
2. NO symbols like **, ++, brackets, or special characters
3. Focus on achievements and quantifiable results
4. Use industry-specific keywords for {target_role}
5. Keep content concise and impactful

Please provide EXACTLY these sections:

SUMMARY:
Write a 3-4 line professional summary highlighting experience relevant to {target_role}

SKILLS:
List relevant technical and soft skills for {target_role} (each skill on new line)

EXPERIENCE:
Rewrite work experience focusing on {target_role} responsibilities and achievements (each point on new line)

PROJECTS:
Describe projects relevant to {target_role} (each project on new line)

EDUCATION:
Educational background (each qualification on new line)

Original Resume:
{original_resume}

Transform this for {target_role} position. Write clearly without any special symbols or formatting.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": professional_prompt}],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.warning(f"AI processing failed: {str(e)}")
        # Return cleaned original content as fallback
        return f"""SUMMARY:
Experienced professional with background relevant to {target_role} position.

SKILLS:
Technical skills and competencies
Professional communication
Problem solving
Team collaboration

EXPERIENCE:
Professional work experience
Relevant project involvement
Achievement-oriented responsibilities

PROJECTS:
Key projects demonstrating {target_role} capabilities
Technical implementations
Problem-solving initiatives

EDUCATION:
Educational qualifications
Relevant coursework
Academic achievements"""

def parse_resume_sections(ai_response):
    """Parse AI response into clean sections"""
    sections = {
        'summary': '',
        'skills': '',
        'experience': '',
        'projects': '',
        'education': ''
    }
    
    # Split by sections with better parsing
    current_section = None
    content_lines = []
    
    for line in ai_response.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check for section headers
        line_lower = line.lower()
        
        if 'summary' in line_lower and ':' in line:
            if current_section and content_lines:
                sections[current_section] = '\n'.join(content_lines)
            current_section = 'summary'
            content_lines = []
            # Get content after colon
            after_colon = line.split(':', 1)[1].strip() if ':' in line else ''
            if after_colon:
                content_lines.append(after_colon)
                
        elif 'skill' in line_lower and ':' in line:
            if current_section and content_lines:
                sections[current_section] = '\n'.join(content_lines)
            current_section = 'skills'
            content_lines = []
            after_colon = line.split(':', 1)[1].strip() if ':' in line else ''
            if after_colon:
                content_lines.append(after_colon)
                
        elif 'experience' in line_lower and ':' in line:
            if current_section and content_lines:
                sections[current_section] = '\n'.join(content_lines)
            current_section = 'experience'
            content_lines = []
            after_colon = line.split(':', 1)[1].strip() if ':' in line else ''
            if after_colon:
                content_lines.append(after_colon)
                
        elif 'project' in line_lower and ':' in line:
            if current_section and content_lines:
                sections[current_section] = '\n'.join(content_lines)
            current_section = 'projects'
            content_lines = []
            after_colon = line.split(':', 1)[1].strip() if ':' in line else ''
            if after_colon:
                content_lines.append(after_colon)
                
        elif 'education' in line_lower and ':' in line:
            if current_section and content_lines:
                sections[current_section] = '\n'.join(content_lines)
            current_section = 'education'
            content_lines = []
            after_colon = line.split(':', 1)[1].strip() if ':' in line else ''
            if after_colon:
                content_lines.append(after_colon)
                
        elif current_section and line:
            content_lines.append(line)
    
    # Add the last section
    if current_section and content_lines:
        sections[current_section] = '\n'.join(content_lines)
    
    return sections

def create_pdf_from_latex(latex_content, filename):
    """Generate professional PDF"""
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = os.path.join(temp_dir, f"{filename}.tex")
        
        # Write LaTeX file with proper encoding
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        try:
            # Compile LaTeX (run twice for better formatting)
            for i in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex_file],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True
                )
            
            pdf_file = os.path.join(temp_dir, f"{filename}.pdf")
            
            if os.path.exists(pdf_file):
                with open(pdf_file, "rb") as f:
                    return f.read(), None
            else:
                return None, result.stderr
                
        except FileNotFoundError:
            return None, "pdflatex not found. Please install LaTeX (MiKTeX/TeXLive)"
        except Exception as e:
            return None, str(e)

# Generate Resume Button
if st.button("🚀 Generate Professional Resume", type="primary", use_container_width=True):
    
    if not resume_text.strip():
        st.error("❌ Pehle resume PDF upload karo!")
    elif selected_role == "Select role...":
        st.error("❌ Target job role select karo!")
    else:
        with st.spinner(f"🔄 Generating professional resume for {selected_role}..."):
            
            # Extract personal information
            name, contact = extract_personal_info(resume_text)
            
            # Generate AI content
            ai_response = generate_professional_resume(resume_text, selected_role)
            
            # Parse sections
            sections = parse_resume_sections(ai_response)
            
            # Create clean LaTeX content
            latex_content = LATEX_TEMPLATE.format(
                name=clean_content(name),
                contact=clean_content(contact),
                summary=clean_content(sections['summary']) if sections['summary'] else "Professional with relevant experience",
                skills=format_as_bullets(sections['skills']),
                experience=format_as_bullets(sections['experience']),
                projects=format_as_bullets(sections['projects']),
                education=format_as_bullets(sections['education'])
            )
            
            # Generate PDF
            safe_filename = re.sub(r'[^a-zA-Z0-9_]', '_', selected_role.replace(' ', '_'))
            pdf_bytes, error = create_pdf_from_latex(latex_content, safe_filename)
            
            if pdf_bytes:
                st.success(f"✅ Professional {selected_role} resume ready!")
                
                # Download button
                st.download_button(
                    label=f"📥 Download {selected_role} Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{safe_filename}_Professional_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Content preview
                with st.expander("👀 Generated Resume Preview"):
                    st.markdown("**Professional Summary:**")
                    st.write(sections['summary'][:200] + "..." if len(sections['summary']) > 200 else sections['summary'])
                    
                    st.markdown("**Skills Preview:**")
                    skills_preview = sections['skills'].replace('\n', ' • ')[:150]
                    st.write(skills_preview + "..." if len(skills_preview) > 150 else skills_preview)
                    
                    st.markdown("**Experience Preview:**")
                    exp_preview = sections['experience'][:200] + "..." if len(sections['experience']) > 200 else sections['experience']
                    st.write(exp_preview)
            
            else:
                st.error(f"❌ PDF generation failed: {error}")
                st.info("💡 Make sure LaTeX is properly installed on your system")

# Help Section
st.markdown("---")
st.markdown("### 💡 How to Use:")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Steps:**
    1. 📁 Upload your current resume PDF
    2. 🎯 Select target job role from dropdown
    3. 🚀 Click generate button
    4. 📥 Download clean, professional PDF
    """)

with col2:
    st.markdown("""
    **Features:**
    ✅ Clean, professional formatting
    ✅ No unwanted symbols or brackets
    ✅ Job role-specific customization
    ✅ ATS-friendly single page layout
    """)

st.markdown("### 🔧 Requirements:")
st.markdown("""
- **LaTeX Installation:** MiKTeX (Windows) / MacTeX (Mac) / TeXLive (Linux)
- **Python Libraries:** `pip install PyPDF2 streamlit groq python-dotenv`
- **API Key:** Set GROQ_API_KEY in your environment variables
""")

st.info("💡 **Pro Tip:** Use specific job roles like 'Python Developer' or 'Digital Marketing Specialist' for better results!")