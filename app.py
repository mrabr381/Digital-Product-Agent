import streamlit as st
import google.generativeai as genai
import io
import time
import re
import os
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
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
</style>
""", unsafe_allow_html=True)


# --- DYNAMIC MODEL FETCHER ---
def get_active_models(api_key: str):
    try:
        genai.configure(api_key=api_key)
        available = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                clean_name = m.name.replace("models/", "")
                if "gemini" in clean_name:
                    available.append(clean_name)
        
        preferred_order = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-2.0-flash-exp", "gemini-pro"]
        sorted_models = [m for m in preferred_order if m in available] + [m for m in available if m not in preferred_order]
        return sorted_models if sorted_models else ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    except Exception:
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]


# --- ROBUST GEMINI CALL WRAPPER (Auto-Retry on 429 Rate Limit) ---
def generate_with_retry(prompt: str, selected_model: str, all_models: list, max_retries: int = 3):
    models_to_try = [selected_model] + [m for m in all_models if m != selected_model]
    
    for current_model in models_to_try:
        model_name_clean = current_model if current_model.startswith("models/") else f"models/{current_model}"
        model = genai.GenerativeModel(model_name=model_name_clean)
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                return response.text, current_model
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "Quota" in err_str or "ResourceExhausted" in err_str:
                    # Extract wait seconds from error message if available
                    match = re.search(r'retry in ([0-9\.]+)s', err_str, re.IGNORECASE)
                    wait_sec = float(match.group(1)) + 0.5 if match else 6.0
                    wait_sec = min(wait_sec, 10.0)
                    
                    st.warning(f"⏳ Rate Limit hit on **{current_model}**. Auto-retrying in {int(wait_sec)}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_sec)
                else:
                    # If other non-retryable error, jump to next model
                    break
    
    raise Exception("Tamam models par quota/rate-limit exceed ho chuka hai. Baraye mehrbani kuch seconds baad dobara try karein.")


# --- PDF SANITIZER FOR REPORTLAB ---
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    # ReportLab uses basic XML tags, so raw ampersands/brackets need escaping
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- PDF GENERATOR UTILITIES ---
def create_ebook_pdf(title, author, content_sections):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=24, leading=28, textColor=colors.HexColor("#1e293b"), spaceAfter=15, alignment=1
    )
    author_style = ParagraphStyle(
        'AuthorStyle', parent=styles['Normal'], fontName='Helvetica-Oblique',
        fontSize=12, leading=15, textColor=colors.HexColor("#64748b"), spaceAfter=30, alignment=1
    )
    h1_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=16, leading=20, textColor=colors.HexColor("#4338ca"), spaceBefore=18, spaceAfter=10
    )
    body_style = ParagraphStyle(
        'BodyDark', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10.5, leading=15, textColor=colors.HexColor("#334155"), spaceAfter=10
    )

    story = [
        Spacer(1, 40),
        Paragraph(sanitize_text(title), title_style),
        Paragraph(f"Created by: {sanitize_text(author)}", author_style),
        Spacer(1, 20)
    ]

    for heading, text in content_sections:
        story.append(Paragraph(sanitize_text(heading), h1_style))
        for p in text.split("\n\n"):
            clean_p = sanitize_text(p.strip().replace("\n", " "))
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
        'PlannerHeader', fontName='Helvetica-Bold', fontSize=20, leading=24,
        textColor=colors.HexColor("#312e81"), alignment=1, spaceAfter=15
    )

    story = [
        Paragraph(f"📋 {sanitize_text(title)}", header_style),
        Paragraph(f"<b>Planner Owner:</b> {sanitize_text(user_name)}", styles['Normal']),
        Spacer(1, 15)
    ]

    # Goals Table
    goals_data = [["No.", "Top Priority Daily Goals", "Status"]]
    for i, g in enumerate(goals, 1):
        goals_data.append([str(i), sanitize_text(g), "[  ] Done"])
    
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
        sched_data.append([sanitize_text(time_slot), sanitize_text(task_desc), ""])
    
    t_sched = Table(sched_data, colWidths=[70, 315, 110])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#ede9fe")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#5b21b6")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Daily Reflections & Notes:</b>", styles['Normal']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(sanitize_text(notes if notes else "Focus on consistent daily execution."), styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("## ⚡ Studio Settings")
    
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("🔑 Gemini API Key", value=default_key, type="password", help="Enter your Gemini API key from Google AI Studio.")
    
    if api_key:
        genai.configure(api_key=api_key)
        available_models = get_active_models(api_key)
    else:
        available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        
    st.markdown("---")
    st.markdown("### ⚙️ Engine Parameters")
    model_choice = st.selectbox("LLM Core (Active on your key)", available_models)
    
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
    st.warning("⚠️ Baraye mehrbani Sidebar mein apni **Gemini API Key** enter karein.")
    st.info("Aap free API key Google AI Studio (aistudio.google.com) se le sakte hain.")
    st.stop()


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
# TAB 1: MARKET RESEARCH
# ==========================================
with tab_research:
    st.subheader("🔍 Digital Product Trend & Market Research")
    st.caption("Search trends, competitor price points, and bestselling digital product ideas.")
    
    col1, col2 = st.columns(2)
    with col1:
        research_query = st.text_input("Enter Niche or Product Idea", placeholder="e.g. printable planners, Notion financial trackers, burnout guides")
    with col2:
        platform = st.selectbox("Target Marketplace", ["Gumroad", "Etsy", "Amazon KDP", "ProductHunt", "Direct Website"])
        
    if st.button("🚀 Analyze Market & Opportunities", key="btn_research"):
        if not research_query:
            st.warning("Query likhna zaroori hai.")
        else:
            with st.spinner(f"Analyzing with {model_choice}..."):
                try:
                    prompt = f"""
                    You are an expert digital product strategist, market analyst, and ecommerce advisor.
                    Conduct a comprehensive, actionable market opportunity analysis for: '{research_query}' to sell on '{platform}'.
                    
                    Structure your response with clear headings:
                    1. 🎯 Target Audience & Core Pain Points
                    2. 💡 Top 3 High-Converting Digital Product Formats (PDF guide, printable planner, Notion template, or code tool)
                    3. 💰 Pricing Strategy & Value Ladders (e.g. $9 starter vs $27 bundle)
                    4. 🚀 Unique Selling Proposition (USP) & Marketing Angles
                    5. 📋 Step-by-Step Launch Blueprint for {platform}
                    
                    Provide concrete, practical, and highly specific ideas without generic fluff.
                    """
                    response_text, used_model = generate_with_retry(prompt, model_choice, available_models)
                    st.markdown(response_text)
                    st.caption(f"⚡ Generated using: `{used_model}`")
                except Exception as e:
                    st.error(f"Error: {e}")


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
        num_chapters = st.slider("Number of Chapters", 2, 5, 3)
        
    if st.button("✨ Draft & Generate Full E-Book", key="btn_ebook"):
        with st.spinner("AI content draft kar raha hai..."):
            try:
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
                raw_text, used_model = generate_with_retry(prompt, model_choice, available_models)
                
                st.success(f"Content generated with `{used_model}`!")
                
                sections = []
                raw_chapters = raw_text.split("### CHAPTER ")
                for rc in raw_chapters:
                    if not rc.strip():
                        continue
                    lines = rc.strip().split("\n", 1)
                    heading = "CHAPTER " + lines[0].strip()
                    body = lines.strip() if len(lines) > 1 else ""
                    sections.append((heading, body))
                
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
        with st.spinner("AI structured planner construct kar raha hai..."):
            try:
                goals = ["Complete key daily priority task", "Deep work focus session (2 hours)", "Physical exercise & wellness routine"]
                schedule = [
                    ("08:00 - 10:00 AM", "Deep Focus & High-Value Output"),
                    ("10:00 - 12:00 PM", "Core Project Execution"),
                    ("01:00 - 02:30 PM", "Meetings & Communications"),
                    ("02:30 - 04:30 PM", "Task Batching & Admin"),
                    ("05:00 - 06:30 PM", "Skill Growth & Exercise"),
                    ("08:00 - 09:00 PM", "Daily Review & Next Day Planning")
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
    c_theme = st.text_input("Design Theme / Purpose", "Modern Dark-Mode Tech Announcement")
    c_brand_colors = st.text_input("Brand Color Preference (Optional)", "Deep Navy Blue, Electric Indigo, Neon Cyan, Pure White")
    
    if st.button("🚀 Generate Canva Design Blueprint", key="btn_canva"):
        with st.spinner("Design architecture compose ho rahi hai..."):
            try:
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
                res_text, used_model = generate_with_retry(prompt, model_choice, available_models)
                st.markdown(res_text)
                
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
                res_text, used_model = generate_with_retry(prompt, model_choice, available_models)
                st.markdown(res_text)
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
                for page in reader.pages[:10]:
                    extracted_text += page.extract_text() or ""
                
                if not extracted_text.strip():
                    st.warning("PDF mein readable text nahi mil saka.")
                else:
                    prompt = f"""
                    You are an expert digital content strategist.
                    Task: {pdf_goal}
                    
                    Here is the text extracted from the document:
                    \"\"\"{extracted_text[:8000]}\"\"\"
                    
                    Provide a comprehensive, high-value breakdown according to the requested action.
                    """
                    res_text, used_model = generate_with_retry(prompt, model_choice, available_models)
                    st.markdown(res_text)
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
