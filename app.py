import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.units import inch
from datetime import datetime
import re
import docx2txt
import PyPDF2
import mammoth

# Set page configuration
st.set_page_config(
    page_title="ResumeAI - Intelligent Resume Tailor",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📄"
)

# Custom CSS for white theme and enhanced UI (keeping same styling as original)
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .info-card {
        background: #ffffff;
        border: 2px solid #e8e8e8;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102,126,234,0.1);
    }
    
    .section-header {
        color: #2c3e50;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 3px solid #667eea;
    }
    
    /* Upload section */
    .upload-section {
        background: #f8f9ff;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    
    /* Result cards */
    .result-card {
        background: #ffffff;
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .result-header {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .result-content {
        color: #34495e;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* Match indicators */
    .match-excellent {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #155724;
    }
    
    .match-good {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #0c5460;
    }
    
    .match-moderate {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #856404;
    }
    
    .match-poor {
        background: #f8d7da;
        border: 1px solid #f1c2c7;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #721c24;
    }
    
    /* Skill tags styling */
    .skill-tag {
        background: #e8f4f8;
        border: 1px solid #b8daff;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 5px;
        display: inline-block;
        color: #004085;
        font-weight: 500;
    }
    
    .skill-missing {
        background: #ffebee;
        border: 1px solid #f44336;
        color: #c62828;
    }
    
    .skill-present {
        background: #e8f5e8;
        border: 1px solid #4caf50;
        color: #2e7d32;
    }
    
    /* Recommendation styling */
    .recommendation-high {
        background: #ffebee;
        border: 2px solid #f44336;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #c62828;
    }
    
    .recommendation-medium {
        background: #fff8e1;
        border: 2px solid #ff9800;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ef6c00;
    }
    
    .recommendation-low {
        background: #f3e5f5;
        border: 2px solid #9c27b0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #7b1fa2;
    }
    
    .recommendation-info {
        background: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #2e7d32;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.4);
    }
    
    /* Disclaimer box */
    .disclaimer {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border-left: 5px solid #ffc107;
    }
    
    .disclaimer strong {
        color: #856404;
        font-size: 1.1rem;
    }
    
    /* Progress and loading */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Text input styling */
    .stTextArea textarea {
        border: 2px solid #e8e8e8;
        border-radius: 8px;
        padding: 12px;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 20px;
        background: #f8f9ff;
    }
    
    /* Metrics styling */
    .metric-card {
        background: white;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .info-card {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

SYSTEM_PROMPT = """
You are an expert HR professional and resume optimization specialist with deep knowledge in applicant tracking systems (ATS), recruitment best practices, and career development.
Your role is to analyze resumes against job descriptions and provide comprehensive, actionable recommendations to improve job match scores while maintaining the original resume format and authenticity.

You have expertise in:
- ATS optimization and keyword matching
- Industry-specific requirements across various sectors
- Resume formatting and structure best practices
- Skill gap analysis and career development
- Interview preparation and job market trends
"""

INSTRUCTIONS = """
Analyze the provided resume against the job description and return detailed insights in the following structured format:

*Match Score:* <percentage score based on alignment>
*Key Strengths:* <specific strengths that align with the job>
*Missing Keywords:* <important keywords/skills missing from resume>
*Skill Gap Analysis:* <detailed analysis of skill gaps>
*Recommended Improvements:* <specific actionable recommendations>
*ATS Optimization Tips:* <tips to improve ATS compatibility>
*Tailored Resume Suggestions:* <specific text additions/modifications while maintaining format>
*Interview Preparation:* <key areas to focus on for interviews>
*Industry Insights:* <relevant industry trends and requirements>
*Next Steps:* <actionable career development steps>

Ensure all recommendations maintain the original resume format and are specific, actionable, and relevant to the target job.
"""

ADDITIONAL_ANALYSIS_PROMPT = """
You are a career development expert specializing in resume optimization and job market analysis.
Provide additional insights on market trends, salary expectations, and competitive positioning for the analyzed resume and job combination.

Focus on:
- Market competitiveness of the candidate's profile
- Salary range expectations for the role
- Career progression opportunities
- Industry-specific advice
- Networking and professional development recommendations
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            instructions=INSTRUCTIONS,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

@st.cache_resource
def get_market_analysis_agent():
    """Initialize and cache the market analysis agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=ADDITIONAL_ANALYSIS_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing market analysis agent: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"📄 Error reading PDF: {e}")
        return None

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file."""
    try:
        # Try using mammoth for better formatting
        result = mammoth.extract_raw_text(docx_file)
        return result.value.strip()
    except Exception:
        try:
            # Fallback to docx2txt
            return docx2txt.process(docx_file).strip()
        except Exception as e:
            st.error(f"📄 Error reading DOCX: {e}")
            return None

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file based on its type."""
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(uploaded_file)
    elif file_extension in ['.docx', '.doc']:
        return extract_text_from_docx(uploaded_file)
    elif file_extension == '.txt':
        return str(uploaded_file.read(), "utf-8")
    else:
        st.error(f"❌ Unsupported file format: {file_extension}")
        return None

def analyze_resume_job_match(resume_text, job_description):
    """Analyze resume against job description using AI."""
    agent = get_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔍 Analyzing resume against job requirements..."):
            query = f"""
            Please analyze this resume against the job description and provide comprehensive optimization recommendations:
            
            RESUME:
            {resume_text}
            
            JOB DESCRIPTION:
            {job_description}
            
            Provide detailed analysis following the structured format specified in the instructions.
            """
            response = agent.run(query)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error analyzing resume: {e}")
        return None

def get_market_insights(resume_text, job_description, analysis_results):
    """Get additional market insights and competitive analysis."""
    market_agent = get_market_analysis_agent()
    if market_agent is None:
        return None

    try:
        with st.spinner("📊 Gathering market insights and competitive analysis..."):
            query = f"""
            Based on this resume and job description analysis, provide market insights:
            
            RESUME: {resume_text[:1000]}...
            JOB DESCRIPTION: {job_description[:500]}...
            ANALYSIS: {analysis_results[:500]}...
            
            Focus on market trends, salary expectations, and competitive positioning.
            """
            response = market_agent.run(query)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error getting market insights: {e}")
        return None

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk."""
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        with NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        return temp_path
    except Exception as e:
        st.error(f"💾 Error saving uploaded file: {e}")
        return None

def create_pdf_report(resume_text, job_description, analysis_results, market_insights=None):
    """Create a PDF report of the resume analysis."""
    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        content = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=18,
            alignment=1,
            spaceAfter=12,
            textColor=colors.navy
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.navy,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=12,
            leading=14
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5,
            backColor=colors.pink,
            alignment=1
        )
        
        # Title
        content.append(Paragraph("📄 ResumeAI - Comprehensive Resume Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Disclaimer
        content.append(Paragraph(
            "⚠️ CAREER DISCLAIMER: This analysis is provided for informational purposes only. "
            "Always conduct your own research and consider professional career counseling for major career decisions.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.25*inch))
        
        # Date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"📅 Generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Job Description Summary
        content.append(Paragraph("🎯 Target Job Description:", heading_style))
        job_desc_preview = job_description[:500] + "..." if len(job_description) > 500 else job_description
        content.append(Paragraph(job_desc_preview.replace('<', '&lt;').replace('>', '&gt;'), normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Analysis results
        content.append(Paragraph("🔍 Resume Analysis Results:", heading_style))
        
        if analysis_results:
            # Parse sections using regex
            sections = [
                ("Match Score", "📊"),
                ("Key Strengths", "💪"),
                ("Missing Keywords", "🔍"),
                ("Skill Gap Analysis", "📈"),
                ("Recommended Improvements", "✨"),
                ("ATS Optimization Tips", "🤖"),
                ("Tailored Resume Suggestions", "📝"),
                ("Interview Preparation", "🎤"),
                ("Industry Insights", "🏭"),
                ("Next Steps", "🚀")
            ]
            
            for section_name, icon in sections:
                pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
                match = re.search(pattern, analysis_results, re.DOTALL | re.IGNORECASE)
                
                if match:
                    section_content = match.group(1).strip()
                    content.append(Paragraph(f"<b>{icon} {section_name}:</b>", normal_style))
                    
                    # Clean content for PDF
                    clean_content = section_content.replace('<', '&lt;').replace('>', '&gt;')
                    paragraphs = clean_content.split("\n")
                    for para in paragraphs:
                        if para.strip():
                            content.append(Paragraph(para.strip(), normal_style))
                    
                    content.append(Spacer(1, 0.15*inch))
        
        # Market insights
        if market_insights:
            content.append(Paragraph("📊 Market Insights & Competitive Analysis:", heading_style))
            clean_insights = market_insights.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_insights, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 ResumeAI - Intelligent Resume Tailor | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        pdf.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_match_score(score_text):
    """Display match score with appropriate styling."""
    try:
        # Extract numeric score if present
        score_match = re.search(r'(\d+)%', score_text)
        if score_match:
            score = int(score_match.group(1))
            if score >= 80:
                st.markdown(f'<div class="match-excellent">🎯 <strong>Excellent Match:</strong> {score_text}</div>', unsafe_allow_html=True)
            elif score >= 60:
                st.markdown(f'<div class="match-good">✅ <strong>Good Match:</strong> {score_text}</div>', unsafe_allow_html=True)
            elif score >= 40:
                st.markdown(f'<div class="match-moderate">⚠️ <strong>Moderate Match:</strong> {score_text}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="match-poor">❌ <strong>Needs Improvement:</strong> {score_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="match-moderate">📊 <strong>Match Score:</strong> {score_text}</div>', unsafe_allow_html=True)
    except:
        st.markdown(f'<div class="match-moderate">📊 <strong>Match Score:</strong> {score_text}</div>', unsafe_allow_html=True)

def display_keywords(keywords_text):
    """Display keywords as styled tags."""
    if not keywords_text:
        return
    
    # Split keywords by common delimiters
    keywords = []
    for delimiter in ['\n', ',', ';', '•', '-']:
        if delimiter in keywords_text:
            keywords = [kw.strip() for kw in keywords_text.split(delimiter) if kw.strip()]
            break
    
    if not keywords:
        keywords = [keywords_text.strip()]
    
    # Display as tags
    tags_html = ""
    for keyword in keywords:
        if keyword:
            tags_html += f'<span class="skill-tag skill-missing">🔍 {keyword}</span>'
    
    if tags_html:
        st.markdown(tags_html, unsafe_allow_html=True)

def display_recommendations(recommendations_text, rec_type):
    """Display recommendations with appropriate styling."""
    if not recommendations_text:
        return
    
    # Determine styling based on type and content
    if "critical" in recommendations_text.lower() or "urgent" in recommendations_text.lower():
        st.markdown(f'<div class="recommendation-high">🚨 <strong>{rec_type}:</strong><br>{recommendations_text}</div>', unsafe_allow_html=True)
    elif "important" in recommendations_text.lower() or "should" in recommendations_text.lower():
        st.markdown(f'<div class="recommendation-medium">⚠️ <strong>{rec_type}:</strong><br>{recommendations_text}</div>', unsafe_allow_html=True)
    elif "consider" in recommendations_text.lower() or "could" in recommendations_text.lower():
        st.markdown(f'<div class="recommendation-low">💡 <strong>{rec_type}:</strong><br>{recommendations_text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="recommendation-info">ℹ️ <strong>{rec_type}:</strong><br>{recommendations_text}</div>', unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = None
    if 'job_description' not in st.session_state:
        st.session_state.job_description = None
    if 'market_insights' not in st.session_state:
        st.session_state.market_insights = None

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📄 ResumeAI</h1>
        <p>Intelligent Resume Tailor & Job Match Optimizer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ CAREER DISCLAIMER</strong><br>
        The recommendations provided by ResumeAI are for informational and educational purposes only. While our AI analyzes your resume against job requirements, career decisions should be made with careful consideration of your personal circumstances. Always consult with career professionals and conduct thorough research before making significant career moves.
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        # Resume upload section
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📄 Upload Your Resume</div>', unsafe_allow_html=True)
        
        resume_file = st.file_uploader(
            "Upload your resume",
            type=["pdf", "docx", "doc", "txt"],
            help="Upload your resume in PDF, DOCX, DOC, or TXT format"
        )
        
        if resume_file:
            file_size = len(resume_file.getvalue()) / 1024  # Convert to KB
            st.success(f"📎 **{resume_file.name}** • {file_size:.1f} KB")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Job description input
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🎯 Target Job Description</div>', unsafe_allow_html=True)
        job_description = st.text_area(
            "Paste the complete job description here:",
            placeholder="Paste the full job description including requirements, responsibilities, qualifications, and any other relevant details...",
            help="Include the complete job posting for better analysis and recommendations",
            height=200
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional preferences
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">⚙️ Analysis Preferences</div>', unsafe_allow_html=True)
        
        col_pref1, col_pref2 = st.columns(2)
        with col_pref1:
            include_salary = st.checkbox("Include Salary Analysis", value=True)
            focus_ats = st.checkbox("Focus on ATS Optimization", value=True)
        
        with col_pref2:
            include_trends = st.checkbox("Include Industry Trends", value=True)
            detailed_feedback = st.checkbox("Detailed Feedback", value=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze button
        if resume_file and job_description:
            if st.button("🚀 Analyze Resume & Get Tailored Recommendations", use_container_width=True):
                st.session_state.analyze_clicked = True
                
                # Extract text from resume
                resume_text = extract_text_from_file(resume_file)
                
                if resume_text:
                    # Store in session state
                    st.session_state.resume_text = resume_text
                    st.session_state.job_description = job_description
                    
                    # Analyze resume
                    analysis_results = analyze_resume_job_match(resume_text, job_description)
                    
                    if analysis_results:
                        st.session_state.analysis_results = analysis_results
                        
                        # Get market insights if requested
                        if include_salary or include_trends:
                            market_insights = get_market_insights(resume_text, job_description, analysis_results)
                            st.session_state.market_insights = market_insights
                        
                        st.success("✅ Comprehensive resume analysis completed!")
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed. Please try again.")
                else:
                    st.error("❌ Could not extract text from resume. Please check the file format.")
    
    with col2:
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            # Parse and display results
            analysis_text = st.session_state.analysis_results
            
            # Enhanced sections list for resume analysis
            sections = [
                ("Match Score", "📊", "match_score"),
                ("Key Strengths", "💪", "strengths"),
                ("Missing Keywords", "🔍", "keywords"),
                ("Skill Gap Analysis", "📈", "analysis"),
                ("Recommended Improvements", "✨", "recommendations"),
                ("ATS Optimization Tips", "🤖", "recommendations"),
                ("Tailored Resume Suggestions", "📝", "suggestions"),
                ("Interview Preparation", "🎤", "preparation"),
                ("Industry Insights", "🏭", "insights"),
                ("Next Steps", "🚀", "recommendations")
            ]
            
            for section_name, icon, section_type in sections:
                # Pattern to match sections
                pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Create result card for each section
                    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-header">{icon} {section_name}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-content">', unsafe_allow_html=True)
                    
                    # Special handling for different section types
                    if section_type == "match_score":
                        display_match_score(content)
                    elif section_type == "keywords":
                        display_keywords(content)
                    elif section_type == "recommendations":
                        display_recommendations(content, section_name)
                    elif section_type == "strengths":
                        # Format strengths as bullet points
                        if '\n' in content or ',' in content:
                            strengths_list = content.replace('\n', ', ').split(',')
                            for strength in strengths_list:
                                if strength.strip():
                                    st.markdown(f"✅ {strength.strip()}")
                        else:
                            st.markdown(f"✅ {content}")
                    elif section_type == "analysis":
                        # Format analysis with proper styling
                        st.markdown(content)
                    elif section_type == "suggestions":
                        # Format suggestions with emphasis
                        suggestions = content.split('\n')
                        for suggestion in suggestions:
                            if suggestion.strip():
                                if suggestion.strip().startswith('-') or suggestion.strip().startswith('•'):
                                    st.markdown(f"📝 {suggestion.strip()[1:].strip()}")
                                else:
                                    st.markdown(f"📝 {suggestion.strip()}")
                    elif section_type == "preparation":
                        # Format interview preparation tips
                        prep_tips = content.split('\n')
                        for tip in prep_tips:
                            if tip.strip():
                                st.markdown(f"🎯 {tip.strip()}")
                    elif section_type == "insights":
                        # Format industry insights
                        st.markdown(f"🏭 {content}")
                    else:
                        st.markdown(content)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Display market insights if available
            if st.session_state.market_insights:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="result-header">📊 Market Insights & Competitive Analysis</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-content">', unsafe_allow_html=True)
                st.markdown(st.session_state.market_insights)
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # PDF download section
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-header">📄 Download Complete Report</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-content">', unsafe_allow_html=True)
            
            pdf_bytes = create_pdf_report(
                st.session_state.resume_text,
                st.session_state.job_description,
                st.session_state.analysis_results,
                st.session_state.market_insights
            )
            if pdf_bytes:
                download_filename = f"resume_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.download_button(
                    label="📥 Download Comprehensive Analysis Report",
                    data=pdf_bytes,
                    file_name=download_filename,
                    mime="application/pdf",
                    help="Download a detailed PDF report with all analysis results and recommendations",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Quick Actions Section
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown('<div class="result-header">⚡ Quick Actions</div>', unsafe_allow_html=True)
            st.markdown('<div class="result-content">', unsafe_allow_html=True)
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if st.button("🔄 Analyze Another Job", use_container_width=True):
                    # Reset analysis but keep resume
                    st.session_state.analysis_results = None
                    st.session_state.market_insights = None
                    st.rerun()
            
            with col_action2:
                if st.button("📄 Upload New Resume", use_container_width=True):
                    # Reset everything
                    st.session_state.analysis_results = None
                    st.session_state.resume_text = None
                    st.session_state.job_description = None
                    st.session_state.market_insights = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            st.markdown("""
            <div class="result-card">
                <div class="result-header">📋 Ready for Analysis</div>
                <div class="result-content">
                    Upload your resume and paste the job description, then click 'Analyze Resume & Get Tailored Recommendations' to see comprehensive results here.
                    <br><br>
                    <strong>What you'll get:</strong>
                    <ul>
                        <li>📊 Job match score and compatibility analysis</li>
                        <li>💪 Key strengths that align with the role</li>
                        <li>🔍 Missing keywords and skills identification</li>
                        <li>📈 Detailed skill gap analysis</li>
                        <li>✨ Specific improvement recommendations</li>
                        <li>🤖 ATS optimization strategies</li>
                        <li>📝 Tailored resume enhancement suggestions</li>
                        <li>🎤 Interview preparation guidance</li>
                        <li>🏭 Industry insights and trends</li>
                        <li>📊 Market analysis and salary expectations</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Resume Optimization Tips Section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">💡 Professional Development Tips</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>🎯 Resume Optimization</h4>
                <ul>
                    <li>Use keywords from the job description naturally</li>
                    <li>Quantify achievements with specific numbers</li>
                    <li>Tailor your resume for each application</li>
                    <li>Optimize for Applicant Tracking Systems (ATS)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-card">
                <h4>🤖 ATS Compatibility</h4>
                <ul>
                    <li>Use standard section headings</li>
                    <li>Avoid complex formatting and graphics</li>
                    <li>Include relevant keywords from job posting</li>
                    <li>Use common file formats (PDF or DOCX)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🎤 Interview Preparation</h4>
                <ul>
                    <li>Research the company and role thoroughly</li>
                    <li>Prepare STAR method examples</li>
                    <li>Practice common behavioral questions</li>
                    <li>Prepare thoughtful questions for the interviewer</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-card">
                <h4>📈 Career Development</h4>
                <ul>
                    <li>Identify and bridge skill gaps</li>
                    <li>Build a strong professional network</li>
                    <li>Stay updated with industry trends</li>
                    <li>Consider relevant certifications</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Key Features Section
    if not st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">🤖</div>
                <div class="metric-label">AI-Powered Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Advanced AI technology for accurate job-resume matching and optimization")
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">🎯</div>
                <div class="metric-label">Tailored Recommendations</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Personalized suggestions to improve your resume for specific job opportunities")
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">📊</div>
                <div class="metric-label">Comprehensive Reports</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Detailed analysis reports with actionable insights and market intelligence")
    
    # Success Stories/Statistics Section
    if not st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">📈 Why Resume Optimization Matters</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">75%</div>
                <div class="metric-label">ATS Rejection Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">6-10s</div>
                <div class="metric-label">Initial Resume Review</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">2.3x</div>
                <div class="metric-label">Higher Interview Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">40%</div>
                <div class="metric-label">Faster Job Placement</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #666;">
            <em>Statistics show that optimized resumes significantly improve job search success rates</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 0.9rem;">
        <p><strong>© 2025 ResumeAI - Intelligent Resume Tailor</strong></p>
        <p>Powered by Gemini AI + Tavily | Built with ❤️ for Job Seekers</p>
        <p><em>Optimize your career journey with data-driven insights</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
