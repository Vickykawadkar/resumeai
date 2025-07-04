# Import necessary classes from PyLaTeX
from pylatex import Document
from pylatex.utils import NoEscape

def convert_latex_string_to_pdf(latex_string: str, filename: str = 'output'):
    """
    Converts a given LaTeX string into a PDF document using PyLaTeX.

    Args:
        latex_string (str): The LaTeX code as a string.
        filename (str): The base name for the output PDF file (e.g., 'my_document' will create 'my_document.pdf').
    """
    try:
        # Create a new document
        doc = Document(documentclass='article', document_options=['10pt', 'a4paper'])

        # Add the raw LaTeX string to the document
        doc.append(NoEscape(latex_string))

        # Generate the PDF
        doc.generate_pdf(filepath=filename, clean_tex=True, compiler='pdflatex')

        print(f"✅ Successfully converted LaTeX string to {filename}.pdf")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("Please ensure you have a LaTeX distribution (like TeX Live or MiKTeX) installed and in your system's PATH.")
        print("You can download TeX Live from: https://www.tug.org/texlive/")
        print("You can download MiKTeX from: https://miktex.org/")



# LaTeX-formatted Resume String
latex_resume_string = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{parskip}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}
\renewcommand\familydefault{\sfdefault}
\titleformat{\section}{\large\bfseries}{}{0em}{}

\begin{document}

\begin{center}
    {\LARGE \textbf{Deepesh Kawadkar}} \\
    Indore, India \\
    \href{mailto:kawadkardeepesh80@gmail.com}{kawadkardeepesh80@gmail.com} \\
    +91 6265366800 \\
    \href{https://linkedin.com/in/deepesh-kawadkar-b7258620b}{linkedin.com/in/deepesh-kawadkar-b7258620b}
\end{center}

\vspace{0.5em}

\section*{Skills}
\begin{itemize}[leftmargin=*]
    \item Programming Languages: C, C++, Core Java, Python, JavaScript
    \item Web Development: HTML, CSS, JSP, Flask, MySQL
    \item Database Management: SQLite
    \item Object-Oriented Programming (OOP)
    \item IoT Development: Arduino, ESP32
    \item Cloud Computing: AWS Cloud Foundation
\end{itemize}

\section*{Education}
\begin{itemize}[leftmargin=*]
    \item \textbf{Bachelor of Technology (B.Tech)} in Information Technology — CGPA: 7.74/10 \\
    Chameli Devi Group of Institutions, Indore (2020 - 2024)
    \item \textbf{12th Grade:} 77.6\% \\
    Career Academy, Indore (2019 - 2020)
    \item \textbf{10th Grade:} 83.0\% \\
    Regal Cambridge Academy, Indore (2017 - 2018)
\end{itemize}

\section*{Projects}

\textbf{Taskify - Task Management System}
\begin{itemize}[leftmargin=*]
    \item A web-based task management system designed to help users create, organize, and manage projects and tasks efficiently.
    \item Allows users to assign tasks to team members based on priority.
    \item Provides an intuitive interface for tracking task progress and managing deadlines.
    \item Enhances collaboration among team members.
    \item \textit{Technologies:} HTML, CSS, JavaScript, Python, Flask, SQLite
    \item \textit{Role:} Full-stack Development, Backend API Integration, Database Design
\end{itemize}

\vspace{0.5em}

\textbf{Restrobook - Restaurant Booking Platform}
\begin{itemize}[leftmargin=*]
    \item A website that helps users find nearby restaurants and book tables directly through the platform.
    \item Search functionality to locate restaurants based on location and preferences.
    \item Integrated booking system for reservations.
    \item Responsive design across devices.
    \item \textit{Technologies:} HTML, CSS, JavaScript, Python, Flask, SQLite
    \item \textit{Role:} Frontend Development, Database Connectivity, UI Design
\end{itemize}

\section*{Work Experience}

\textbf{Intern, Platforma IT Solutions Pvt Ltd} (Aug 2023) \\
Focused on frontend development and IoT solutions using HTML, CSS, Java, JSP, Arduino, and ESP32. \\
Designed responsive web interfaces and developed IoT modules for remote monitoring and control.

\vspace{0.5em}

\textbf{Online Internship, IIT Indore} (Jan 2022) \\
Developed and optimized a perceptron neural network for classifying odd numbers. \\
Improved accuracy with data preprocessing and hyperparameter tuning.

\end{document}
"""

# Generate Resume PDF
if __name__ == "__main__":
    convert_latex_string_to_pdf(latex_resume_string, "DeepeshKawadkar_Resume")
