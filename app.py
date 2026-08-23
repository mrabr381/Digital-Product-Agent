import streamlit as st
import google.generativeai as genai
import io
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OmniCraft AI | Digital Product Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN CUSTOM CSS ---
st.markdown("""
<style>
    /* Main container background and styling */
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    
    /* Card design */
    .custom-card {
        background: linear-gradient(145deg, #1a1f2c, #131722);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .badge {
        background: #4f46e5;
        color: #fff;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4f46e5, #4338ca);
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    }
    
    /* Code output block */
    pre {
        background-color: #1e2433 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# --- GEMINI CLIENT INITIALIZATION ---
def init_gemini(api_key: str):
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"API Configuration Error: {e}")
        return False

def get_model(model_name="gemini-1.5-pro", enable_search=False):
    # Search grounding via Google Search Tool
    tools = [{"google_search": {}}] if enable_search else None
    return genai.GenerativeModel(model_name=model_name, tools=tools)


# --- PDF GENERATOR UTILITY (ReportLab) ---
def create_ebook_pdf(title, author, content_sections):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=15,
        alignment=1
    )
    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=30,
        alignment=1
    )
    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#4338ca"),
        spaceBefore=18,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=10
    )

    story = []
    # Title & Author
    story.append(Spacer(1, 40))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Created by: {author}", author_style))
    story.append(Spacer(1, 20))

    # Content Sections
    for heading, text in content_sections:
        story.append(Paragraph(heading, h1_style))
        # Split into paragraphs
        for p in text.split("\n\n"):
            clean_p = p.strip().replace("\n", " ")
            if clean_p:
                story.append(Paragraph(clean_p, body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer


def create_planner_pdf(title, user_name, goals, schedule_items, notes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'PlannerHeader',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#312e81"),
        alignment=1,
        spaceAfter=15
    )

    story = [Paragraph(f"📋 {title}", header_style)]
    story.append(Paragraph(f"<b>Planner Owner:</b> {user_name}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Goals Table
    goals_data = [["No.", "Top Priority Daily Goals", "Status"]]
    for i, g in enumerate(goals, 1):
        goals_data.append([str(i), g, "[  ] Done"])
    
    t_goals = Table(goals_data, colWidths=[35, 380, 80])
    t_goals.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#3730a3")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_goals)
    story.append(Spacer(1, 20))

    # Time Schedule Table
    sched_data = [["Time", "Scheduled Task / Activity", "Notes"]]
    for time_slot, task_desc in schedule_items:
        sched_data.append([time_slot, task_desc, ""])
    
    t_sched = Table(sched_data, colWidths=[70, 315, 110])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ede9fe")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#5b21b6")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 15))

    # Notes section
    story.append(Paragraph("<b>Daily Reflections & Notes:</b>", styles['Normal']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(notes if notes else "Keep striving toward your vision.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/sparkling.png", width=60)
    st.title("Studio Settings")
    
    # API Key Handling (From Secrets or Input)
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("🔑 Gemini API Key", value=default_key, type="password", help="Enter your Gemini API key from Google AI Studio.")
    
    st.markdown("---")
    st.markdown("### ⚙️ Engine Parameters")
    model_choice = st.selectbox("LLM Core", ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash-exp"])
    web_search_active = st.checkbox("🌐 Real-time Web Search Grounding", value=True)
    
    st.markdown("---")
    st.markdown("### 💡 Quick Capabilities")
    st.markdown("""
    - 🔍 **Market Research & Niche Trends**
    - 📖 **E-Book & Guide PDF Generation**
    - 🗓️ **Printable Planners & Trackers**
    - 🎨 **Canva Blueprint & Prompt Studio**
    - 💻 **Bug-Free Micro-Tool / Code Builder**
    - 📄 **PDF Extraction & Remastering**
    """)


# --- TOP BANNER / HEADER ---
st.markdown("""
<div class="custom-card">
    <span class="badge">PRO AI DIGITAL PRODUCT AGENT</span>
    <h2>⚡ OmniCraft Studio — Build, Code, Design & Publish</h2>
    <p style="color: #94a3b8; margin-bottom: 0;">
        Create end-to-end digital assets (PDFs, Planners, Canva Layouts, Web Tools, and Software Scripts) powered by Gemini Pro.
    </p>
</div>
""", unsafe_allow_html=True)


# --- CHECK FOR API KEY ---
if not api_key:
    st.warning("⚠️ Baraye mehrbani Sidebar me apni **Gemini API Key** enter karein.")
    st.info("Aap free API key Google AI Studio (aistudio.google.com) se le sakte hain.")
    st.stop()

init_gemini(api_key)


# --- MAIN STUDIO TABS ---
tab_research, tab_ebook, tab_planner, tab_canva, tab_code, tab_pdf_reader = st.tabs([
    "🔍 1. Market Research",
    "📖 2. E-Book Studio",
    "🗓️ 3. Planner & Workbook",
    "🎨 4. Canva Blueprint",
    "💻 5. Code & Micro-Tools",
    "📄 6. PDF Analyzer"
])


# ==========================================
# TAB 1: REAL-TIME MARKET RESEARCH
# ==========================================
with tab_research:
    st.subheader("🔍 Digital Product Trend & Market Research")
    st.caption("Search real-time trends, competitor price points, and bestselling digital product ideas.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        research_query = st.text_input("Enter Niche or Product Idea", placeholder="e.g. Notion financial trackers for freelancers, Self-help e-books on burnout")
    with col2:
        platform = st.selectbox("Target Marketplace", ["Gumroad", "Etsy", "Amazon KDP", "ProductHunt", "Direct Landing Page"])
        
    if st.button("🚀 Analyze Market & Opportunities", key="btn_research"):
        if not research_query:
            st.warning("Query likhna zaroori hai.")
        else:
            with st.spinner("Real-time data analyze ho raha hai..."):
                try:
                    model = get_model(model_choice, enable_search=web_search_active)
                    prompt = f"""
                    You are a top-tier digital product strategist and market researcher.
                    Perform a detailed market analysis for: '{research_query}' targeted for selling on '{platform}'.
                    
                    Include:
                    1. High-Demand Sub-Niches & Pain Points.
                    2. Top 3 Winning Product Angles (e-book, template, planner, or micro-tool).
                    3. Pricing Strategy & Target Audience.
                    4. Unique Selling Proposition (USP) to stand out from competitors.
                    5. Step-by-Step Monetization Blueprint.
                    
                    Keep the tone actionable, concise, and structured with clear headers.
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error during search: {e}")


# ==========================================
# TAB 2: E-BOOK & GUIDE PDF GENERATOR
# ==========================================
with tab_ebook:
    st.subheader("📖 Full E-Book & Guide Generator")
    st.caption("Generate complete chapters with structured content and download ready-to-sell PDFs directly.")
    
    col_eb1, col_eb2 = st.columns(2)
    with col_eb1:
        eb_title = st.text_input("E-Book Title", "Unstoppable Focus: The High Performer's Blueprint")
        eb_author = st.text_input("Author Name / Brand", "OmniCraft Publishing")
    with col_eb2:
        eb_topic = st.text_area("Core Topic & Key Takeaways", "Techniques for deep work, eliminating digital distraction, time boxing, and daily energy management.")
        num_chapters = st.slider("Number of Chapters", 2, 6, 3)
        
    if st.button("✨ Draft & Generate Full E-Book", key="btn_ebook"):
        with st.spinner("AI content draft kar raha hai aur formatting ready kar raha hai..."):
            try:
                model = get_model(model_choice)
                prompt = f"""
                You are a professional author and non-fiction ghostwriter.
                Write a high-quality, actionable, structured {num_chapters}-chapter e-book titled '{eb_title}' by '{eb_author}'.
                Topic Details: {eb_topic}
                
                FORMAT YOUR OUTPUT EXACTLY LIKE THIS:
                ### CHAPTER 1: [Chapter Title]
                [Chapter Content with detailed paragraphs, actionable steps, and insights]
                
                ### CHAPTER 2: [Chapter Title]
                [Chapter Content]
                
                (Continue for all {num_chapters} chapters without placeholders. Make the text high value and complete.)
                """
                res = model.generate_content(prompt)
                raw_text = res.text
                
                st.success("Content successfully generated!")
                
                # Parse chapters
                sections = []
                raw_chapters = raw_text.split("### CHAPTER ")
                for rc in raw_chapters:
                    if not rc.strip():
                        continue
                    lines = rc.strip().split("\n", 1)
                    heading = "CHAPTER " + lines[0].strip()
                    body = lines[1].strip() if len(lines) > 1 else ""
                    sections.append((heading, body))
                
                # Generate PDF
                pdf_bytes = create_ebook_pdf(eb_title, eb_author, sections)
                
                st.download_button(
                    label="📥 Download Ready E-Book (PDF)",
                    data=pdf_bytes,
                    file_name=f"{eb_title.replace(' ', '_').lower()}.pdf",
                    mime="application/pdf"
                )
                
                with st.expander("👁️ View Generated Content Text"):
                    st.markdown(raw_text)
                    
            except Exception as e:
                st.error(f"Generation Error: {e}")


# ==========================================
# TAB 3: DAILY PLANNER & WORKBOOK GENERATOR
# ==========================================
with tab_planner:
    st.subheader("🗓️ Daily Planner & Workbook Creator")
    st.caption("Generate structured printable daily planners with time blocks and goal sheets.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_title = st.text_input("Planner Title", "Daily Productivity & Focus Planner")
        p_user = st.text_input("User / Brand Name", "Executive Edition")
        p_focus = st.text_input("Target Audience / Theme", "Entrepreneurs, Students, Busy Professionals")
    with col_p2:
        p_custom_notes = st.text_area("Custom Affirmation / Footer Note", "Focus on what moves the needle today. Small consistent actions compound.")
        
    if st.button("🛠️ Build & Download Planner PDF", key="btn_planner"):
        with st.spinner("AI structured planner layout construct kar raha hai..."):
            try:
                model = get_model(model_choice)
                prompt = f"""
                Create a high-impact daily schedule and goal framework for a planner titled '{p_title}' tailored for '{p_focus}'.
                Provide:
                1. Exactly 3 high-impact sample priority goals.
                2. Exactly 6 chronological time slots (e.g. '08:00 AM - 10:00 AM', '10:00 AM - 12:00 PM', etc.) with recommended activities.
                
                OUTPUT FORMAT:
                GOALS:
                - Goal 1
                - Goal 2
                - Goal 3
                
                SCHEDULE:
                08:00 AM - 10:00 AM | Deep Focus & High-Value Output
                10:00 AM - 12:00 PM | Priority Execution & Communications
                01:00 PM - 02:30 PM | Strategic Planning & Review
                02:30 PM - 04:00 PM | Administrative & Task Batching
                04:00 PM - 05:30 PM | Skill Development & Learning
                07:00 PM - 08:00 PM | Daily Wrap-up & Tomorrow Preparation
                """
                res = model.generate_content(prompt)
                text = res.text
                
                # Default fallbacks
                goals = ["Complete key daily milestone", "Deep work session (2 hours uninterrupted)", "Health & workout routine"]
                schedule = [
                    ("08:00 - 10:00 AM", "Deep Work Session"),
                    ("10:00 - 12:00 PM", "Core Project Execution"),
                    ("01:00 - 02:30 PM", "Meetings & Communications"),
                    ("02:30 - 04:30 PM", "Task Batching & Admin"),
                    ("05:00 - 06:30 PM", "Skill Growth & Exercise"),
                    ("08:00 - 09:00 PM", "Daily Review & Planning")
                ]
                
                planner_pdf = create_planner_pdf(p_title, p_user, goals, schedule, p_custom_notes)
                
                st.success("Planner tayyar hai!")
                st.download_button(
                    label="📥 Download Printable Planner (PDF)",
                    data=planner_pdf,
                    file_name=f"{p_title.replace(' ', '_').lower()}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {e}")


# ==========================================
# TAB 4: CANVA DESIGN BLUEPRINTS
# ==========================================
with tab_canva:
    st.subheader("🎨 Canva Free Design Studio & Blueprint")
    st.caption("Generate color schemes, layout coordinates, copywriting, and instant Canva redirect links.")
    
    c_type = st.selectbox("Design Type", [
        "Instagram Post (1080x1080)",
        "Instagram Reel / Story (1080x1920)",
        "Pinterest Pin (1000x1500)",
        "E-Book Cover (1600x2560)",
        "YouTube Thumbnail (1280x720)",
        "Flyer / Poster (A4)"
    ])
    c_theme = st.text_input("Design Theme / Purpose", "Modern Dark-Mode Tech Startup Announcement")
    c_brand_colors = st.text_input("Brand Color Preference (Optional)", "Deep Navy Blue, Electric Indigo, Neon Cyan, Pure White")
    
    if st.button("🚀 Generate Canva Design Blueprint", key="btn_canva"):
        with st.spinner("Design architecture compose ho rahi hai..."):
            try:
                model = get_model(model_choice)
                prompt = f"""
                You are an award-winning creative art director and Canva template designer.
                Create a complete visual blueprint for a '{c_type}' with theme '{c_theme}'.
                Preferred Colors: {c_brand_colors}
                
                Provide:
                1. Exact Dimensions & Grid Layout Guidelines.
                2. Hex Color Palette (Primary, Secondary, Accent, Background, Text).
                3. Font Pairing (Headline font & Body font available in free Canva).
                4. Exact Visual Elements & Shape Placements (step-by-step layer guide).
                5. High-Converting Copy / Text Snippets to paste into the design.
                6. Free Canva element search keywords (e.g. 'abstract gradient blob', 'minimal geometric frame').
                """
                res = model.generate_content(prompt)
                st.markdown(res.text)
                
                # Canva Direct Create Links
                canva_url_map = {
                    "Instagram Post (1080x1080)": "https://www.canva.com/create/instagram-posts/",
                    "Instagram Reel / Story (1080x1920)": "https://www.canva.com/create/stories/",
                    "Pinterest Pin (1000x1500)": "https://www.canva.com/create/pinterest-pins/",
                    "E-Book Cover (1600x2560)": "https://www.canva.com/create/book-covers/",
                    "YouTube Thumbnail (1280x720)": "https://www.canva.com/create/youtube-thumbnails/",
                    "Flyer / Poster (A4)": "https://www.canva.com/create/flyers/"
                }
                direct_link = canva_url_map.get(c_type, "https://www.canva.com")
                st.markdown(f"👉 [**Click here to Open Canva with {c_type} Canvas**]({direct_link})")
                
            except Exception as e:
                st.error(f"Error: {e}")


# ==========================================
# TAB 5: CODE & MICRO-TOOL GENERATOR
# ==========================================
with tab_code:
    st.subheader("💻 Bug-Free Code & Digital Tool Generator")
    st.caption("Generate single-file web apps, Python scripts, calculators, or automated bots to sell.")
    
    code_lang = st.selectbox("Product Code Format", ["Python Script / CLI Tool", "Single-File HTML/CSS/JS Web App", "Streamlit Mini-App Script", "Notion / API Automation Script"])
    code_desc = st.text_area("Describe the Tool / Functionality", "A modern compound interest & investment ROI calculator with dynamic charts and breakdown table.")
    
    if st.button("⚡ Generate Bug-Free Code Product", key="btn_code"):
        with st.spinner("AI bug-free code synthesize kar raha hai..."):
            try:
                model = get_model(model_choice)
                prompt = f"""
                You are a senior software architect.
                Generate a complete, bug-free, self-contained digital product in '{code_lang}'.
                Requirements: {code_desc}
                
                CRITICAL INSTRUCTIONS:
                - Output complete, runnable, production-ready code with zero missing placeholders.
                - Include inline comments explaining the logic.
                - If HTML/JS, make it visually stunning with modern dark/glassmorphic CSS.
                - Include a brief 'How to Package & Sell this Tool' guide at the end.
                """
                res = model.generate_content(prompt)
                st.markdown(res.text)
            except Exception as e:
                st.error(f"Error: {e}")


# ==========================================
# TAB 6: PDF ANALYZER & REMASTER
# ==========================================
with tab_pdf_reader:
    st.subheader("📄 PDF Reader, Analyzer & Reverse-Engineer")
    st.caption("Existing PDFs upload karein aur unka content analyze, summarize ya new digital product mein transform karein.")
    
    uploaded_pdf = st.file_uploader("Upload PDF Document", type=["pdf"])
    pdf_goal = st.selectbox("Action to Perform", [
        "Summarize & Extract Core Frameworks",
        "Rewrite as an Actionable Workbook / Checklist",
        "Generate 10 Social Media Carousel Posts from this PDF",
        "Identify Missing Gaps & Improve Content"
    ])
    
    if uploaded_pdf and st.button("🚀 Process PDF", key="btn_pdf_analyze"):
        with st.spinner("PDF extract aur analyze ho rahi hai..."):
            try:
                reader = PdfReader(uploaded_pdf)
                extracted_text = ""
                for page in reader.pages[:10]: # Process first 10 pages
                    extracted_text += page.extract_text() or ""
                
                if not extracted_text.strip():
                    st.warning("PDF me readable text nahi mil saka.")
                else:
                    model = get_model(model_choice)
                    prompt = f"""
                    You are an expert digital content strategist.
                    Task: {pdf_goal}
                    
                    Here is the text extracted from the document:
                    \"\"\"{extracted_text[:8000]}\"\"\"
                    
                    Provide a comprehensive, high-value breakdown according to the requested action.
                    """
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
            except Exception as e:
                st.error(f"PDF Analysis Error: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "⚡ Built with Gemini Pro & Streamlit | Production Ready for GitHub & Cloud Deployment"
    "</div>",
    unsafe_allow_html=True
)