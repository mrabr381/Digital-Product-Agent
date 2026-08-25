import streamlit as st
import google.generativeai as genai
import io
import time
import re
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="OmniCraft AI | Complete Digital Product Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    .custom-card {
        background: linear-gradient(145deg, #1e2433, #131722);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .badge {
        background: #4f46e5;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 14px;
        font-size: 0.82rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 10px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #4f46e5);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4f46e5, #4338ca);
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
    }
</style>
""", unsafe_allow_html=True)


# --- REPORTLAB CANVAS WITH AUTOMATIC PAGE NUMBERING ---
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        page_w, page_h = letter  # Clean tuple unpacking: (612.0, 792.0)
        if self._pageNumber > 1: # Suppress header/footer on Cover Page
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(40, page_h - 30, "OFFICIAL DIGITAL PRODUCT SUITE")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, page_h - 35, page_w - 40, page_h - 35)

            # Footer
            self.drawRightString(page_w - 40, 25, f"Page {self._pageNumber} of {page_count}")
            self.drawString(40, 25, "Confidential & Exclusive Content | All Rights Reserved")
            self.line(40, 36, page_w - 40, 36)
        self.restoreState()


# --- SANITIZE STRINGS FOR REPORTLAB ---
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- PREMIUM E-BOOK PDF ENGINE ---
def build_pro_ebook(title, author, subtitle, chapters):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=45, leftMargin=45, topMargin=50, bottomMargin=50
    )
    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0f172a")
    SECONDARY = colors.HexColor("#4f46e5")
    LIGHT_ACCENT = colors.HexColor("#e0e7ff")
    TEXT_DARK = colors.HexColor("#1e293b")
    TEXT_MUTED = colors.HexColor("#64748b")

    cover_title = ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=26, leading=32, textColor=PRIMARY, alignment=1, spaceAfter=12)
    cover_sub = ParagraphStyle('CoverSub', fontName='Helvetica', fontSize=13, leading=17, textColor=SECONDARY, alignment=1, spaceAfter=20)
    cover_auth = ParagraphStyle('CoverAuth', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=TEXT_MUTED, alignment=1)
    
    chap_badge = ParagraphStyle('ChapBadge', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=SECONDARY, spaceBefore=8, spaceAfter=4)
    chap_title = ParagraphStyle('ChapTitle', fontName='Helvetica-Bold', fontSize=17, leading=21, textColor=PRIMARY, spaceAfter=10)
    body_style = ParagraphStyle('EbookBody', fontName='Helvetica', fontSize=10, leading=15, textColor=TEXT_DARK, spaceAfter=8)
    callout_style = ParagraphStyle('Callout', fontName='Helvetica-Oblique', fontSize=9.5, leading=14, textColor=colors.HexColor("#312e81"))

    story = []

    # Cover Page
    story.append(Spacer(1, 90))
    story.append(Paragraph(sanitize_text(title.upper()), cover_title))
    story.append(HRFlowable(width="60%", thickness=2, color=SECONDARY, spaceBefore=8, spaceAfter=12))
    story.append(Paragraph(sanitize_text(subtitle), cover_sub))
    story.append(Spacer(1, 160))
    story.append(Paragraph(f"Created by: <b>{sanitize_text(author)}</b>", cover_auth))
    story.append(Spacer(1, 4))
    story.append(Paragraph("A Masterclass Publication & Practical Framework", ParagraphStyle('SubSub', fontName='Helvetica', fontSize=8.5, leading=11, textColor=TEXT_MUTED, alignment=1)))
    story.append(PageBreak())

    # Chapters
    for idx, (ch_title, ch_content) in enumerate(chapters, 1):
        story.append(Paragraph(f"SECTION 0{idx} // STRATEGY", chap_badge))
        story.append(Paragraph(sanitize_text(ch_title), chap_title))
        story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_ACCENT, spaceBefore=4, spaceAfter=12))

        paras = [p.strip() for p in ch_content.split("\n\n") if p.strip()]
        for p in paras:
            if p.startswith(">") or "Key Takeaway:" in p or "Pro Tip:" in p:
                clean_c = sanitize_text(p.replace(">", "").strip())
                t_call = Table([[Paragraph(clean_c, callout_style)]], colWidths=[520])
                t_call.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), LIGHT_ACCENT),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                    ('RIGHTPADDING', (0,0), (-1,-1), 12),
                    ('TOPPADDING', (0,0), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                    ('LINELEFT', (0,0), (0,0), 3, SECONDARY),
                ]))
                story.append(t_call)
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(sanitize_text(p), body_style))

        if idx < len(chapters):
            story.append(PageBreak())

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


# --- PREMIUM PLANNER PDF ENGINE ---
def build_pro_planner(title, owner_name, goals, schedule_items, notes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=40
    )
    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#1e1b4b")
    SECONDARY = colors.HexColor("#4f46e5")
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    TEXT_MAIN = colors.HexColor("#0f172a")
    TEXT_MUTED = colors.HexColor("#64748b")

    header_style = ParagraphStyle('PlannerTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=PRIMARY)
    meta_style = ParagraphStyle('MetaStyle', fontName='Helvetica', fontSize=8.5, leading=12, textColor=TEXT_MAIN, alignment=2)
    sec_title = ParagraphStyle('SecTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=SECONDARY, spaceBefore=4, spaceAfter=4)

    c_bold = ParagraphStyle('CBold', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=PRIMARY)
    c_norm = ParagraphStyle('CNorm', fontName='Helvetica', fontSize=8.5, leading=11, textColor=TEXT_MAIN)
    c_time = ParagraphStyle('CTime', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=SECONDARY, alignment=1)
    c_done = ParagraphStyle('CDone', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=TEXT_MUTED, alignment=1)

    story = []

    # Header Row
    top_table = Table([
        [
            Paragraph(sanitize_text(title.upper()), header_style),
            Paragraph(f"<b>Owner:</b> {sanitize_text(owner_name)}<br/><b>Date:</b> ______________", meta_style)
        ]
    ], colWidths=[370, 170])
    top_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=2, spaceAfter=8))

    # Priority Outcomes Table
    goals_data = [
        [Paragraph("TOP 3 DAILY CORE PRIORITIES", c_bold), Paragraph("TARGET TIME", c_bold), Paragraph("DONE", c_bold)]
    ]
    for i, g in enumerate(goals[:3], 1):
        target_t = "09:00 AM" if i==1 else ("01:30 PM" if i==2 else "04:30 PM")
        goals_data.append([
            Paragraph(f"<b>{i}.</b> {sanitize_text(g)}", c_norm),
            Paragraph(target_t, c_norm),
            Paragraph("[  ]", c_done)
        ])
    
    t_goals = Table(goals_data, colWidths=[370, 110, 60])
    t_goals.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0e7ff")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_goals)
    story.append(Spacer(1, 10))

    # Hourly Execution Blocks Table
    story.append(Paragraph("HOURLY EXECUTION BLOCKS", sec_title))
    sched_data = [
        [Paragraph("TIME BLOCK", c_bold), Paragraph("ACTIONABLE FOCUS TASK", c_bold), Paragraph("STATUS / NOTES", c_bold)]
    ]
    for time_slot, task_desc in schedule_items:
        sched_data.append([
            Paragraph(sanitize_text(time_slot), c_time),
            Paragraph(sanitize_text(task_desc), c_norm),
            Paragraph("High Focus", c_norm)
        ])
    
    t_sched = Table(sched_data, colWidths=[120, 310, 110])
    t_sched.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 10))

    # Daily Reflection Box
    notes_data = [
        [Paragraph("DAILY REFLECTION & WIN OF THE DAY", c_bold)],
        [Paragraph(f"<i>{sanitize_text(notes if notes else 'Focus on what moves the needle today. Small consistent actions compound.')}</i><br/><br/>", c_norm)]
    ]
    t_notes = Table(notes_data, colWidths=[540])
    t_notes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_notes)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


# --- SAFE E-BOOK CHAPTER PARSER ---
def parse_ebook_chapters(raw_text: str):
    chapters = []
    lines = raw_text.strip().split("\n")
    current_title = ""
    current_content = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("### chapter") or stripped.lower().startswith("## chapter") or stripped.lower().startswith("# chapter"):
            if current_title and current_content:
                chapters.append((current_title, "\n".join(current_content).strip()))
                current_content = []
            
            clean_title = stripped.lstrip("#").replace("CHAPTER", "").replace("Chapter", "").strip(": -").strip()
            current_title = clean_title if clean_title else f"Chapter {len(chapters) + 1}"
        else:
            if current_title:
                current_content.append(line)
                
    if current_title and current_content:
        chapters.append((current_title, "\n".join(current_content).strip()))
        
    if not chapters:
        chapters.append(("Core Framework & Action Guide", raw_text.strip()))
        
    return chapters


# --- SAFE BUNDLE DELIMITER PARSER ---
def parse_bundle_response(raw_text: str):
    code_html = ""
    canva_blueprint = ""
    sales_copy = ""

    web_match = re.search(r'=== WEB_APP_START ===(.*?)=== WEB_APP_END ===', raw_text, re.DOTALL)
    if web_match:
        code_html = web_match.group(1).strip()
    else:
        html_block = re.search(r'```(?:html)?\s*(<!DOCTYPE html>.*?)```', raw_text, re.DOTALL | re.IGNORECASE)
        if html_block:
            code_html = html_block.group(1).strip()
        else:
            code_html = "<!DOCTYPE html><html><head><title>Productivity Tool</title><style>body{font-family:sans-serif;background:#0f172a;color:white;padding:30px;}</style></head><body><h2>⚡ Interactive Focus Tool</h2><p>Custom tool ready for launch.</p></body></html>"

    canva_match = re.search(r'=== CANVA_START ===(.*?)=== CANVA_END ===', raw_text, re.DOTALL)
    if canva_match:
        canva_blueprint = canva_match.group(1).strip()
    else:
        canva_blueprint = "### 🎨 Canva Marketing Blueprint\n- **Hex Palette:** `#0f172a`, `#4f46e5`, `#06b6d4`, `#f8fafc`\n- **Typography:** Montserrat Bold (Headlines) & Lato Regular (Body)"

    sales_match = re.search(r'=== SALES_COPY_START ===(.*?)=== SALES_COPY_END ===', raw_text, re.DOTALL)
    if sales_match:
        sales_copy = sales_match.group(1).strip()
    else:
        sales_copy = "### 🚀 Product Launch Copy\nHigh converting description ready for Gumroad and Etsy."

    return code_html, canva_blueprint, sales_copy


# --- RESEARCH & SUB-NICHE JSON PARSER ---
def parse_research_and_niches(raw_text: str):
    sub_niches = []
    clean_report = raw_text
    
    json_match = re.search(r'=== JSON_START ===(.*?)=== JSON_END ===', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1).strip())
            if "sub_niches" in data and isinstance(data["sub_niches"], list):
                sub_niches = data["sub_niches"]
            clean_report = raw_text.replace(json_match.group(0), "").strip()
        except Exception:
            pass
            
    if not sub_niches:
        sub_niches = [
            {
                "name": "Burnout Recovery & Deep Work Mastery for Freelancers",
                "title": "UNSTOPPABLE FOCUS: The Freelancer's Deep Work Blueprint",
                "subtitle": "Eliminate Digital Distractions, Build Consistent Daily Output & Double Revenue",
                "price": "$19 - $29"
            },
            {
                "name": "High-Performance Morning & Timeboxing Systems",
                "title": "THE 3-HOUR WORKDAY: Timeboxing Architecture for High Achievers",
                "subtitle": "How to Accomplish 8 Hours of High-Leverage Output in 180 Minutes",
                "price": "$24 - $37"
            },
            {
                "name": "Digital Asset & Notion Systemization for Creators",
                "title": "SYSTEMIZE & SCALE: The Digital Creator's Operational Toolkit",
                "subtitle": "Streamline Content Sprints, Client Workflows and Daily Execution",
                "price": "$27 - $49"
            }
        ]
        
    return clean_report, sub_niches


# --- STRICT TEXT-ONLY MODEL FILTER ---
def get_active_models(api_key: str):
    try:
        genai.configure(api_key=api_key)
        valid_models = []
        excluded_keywords = ["tts", "embedding", "aqa", "imagen", "audio", "vision-preview"]
        
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                clean_name = m.name.replace("models/", "")
                if "gemini" in clean_name and not any(ex in clean_name.lower() for ex in excluded_keywords):
                    valid_models.append(clean_name)
        
        preferred_order = [
            "gemini-1.5-flash", "gemini-1.5-flash-latest",
            "gemini-1.5-pro", "gemini-1.5-pro-latest",
            "gemini-2.0-flash-exp", "gemini-1.5-flash-8b", "gemini-pro"
        ]
        sorted_models = [m for m in preferred_order if m in valid_models] + [m for m in valid_models if m not in preferred_order]
        return sorted_models if sorted_models else ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    except Exception:
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]


# --- ROBUST GEMINI CALL ---
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
                    match = re.search(r'retry in ([0-9\.]+)s', err_str, re.IGNORECASE)
                    wait_sec = float(match.group(1)) + 0.5 if match else 5.0
                    wait_sec = min(wait_sec, 8.0)
                    st.info(f"⏳ Rate limit handled. Auto-retrying with `{current_model}` in {int(wait_sec)}s...")
                    time.sleep(wait_sec)
                else:
                    break
    raise Exception("Rate limit reached. Please wait a few moments and try again.")


# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.markdown("## ⚡ Studio Control Panel")
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("🔑 Gemini API Key", value=default_key, type="password")
    
    if api_key:
        genai.configure(api_key=api_key)
        available_models = get_active_models(api_key)
    else:
        available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        
    st.markdown("---")
    model_choice = st.selectbox("Active AI Core", available_models, index=0)
    st.caption("💡 `gemini-1.5-flash` is fast & has highest request limits.")


# --- TOP BANNER ---
st.markdown("""
<div class="custom-card">
    <span class="badge">END-TO-END AUTOMATED PIPELINE</span>
    <h2>⚡ OmniCraft Studio — Full Digital Product Builder</h2>
    <p style="color: #94a3b8; margin-bottom: 0;">
        Research any niche, auto-select a winning sub-niche, and automatically generate a complete <b>Ready-to-Sell Product Bundle</b> (PDFs, Planners, Web Tools, Canva Assets & Sales Copy).
    </p>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.warning("⚠️ Baraye mehrbani Sidebar mein apni **Gemini API Key** enter karein.")
    st.stop()


# --- SESSION STATE INITIALIZATION ---
if "research_report" not in st.session_state:
    st.session_state.research_report = None
if "extracted_niches" not in st.session_state:
    _, st.session_state.extracted_niches = parse_research_and_niches("")
if "bundle_data" not in st.session_state:
    st.session_state.bundle_data = None


# --- WORKFLOW TABS ---
tab_step1, tab_step2, tab_step3 = st.tabs([
    "🔍 Step 1: Market Research",
    "🎯 Step 2: Auto-Extract & Configure",
    "📦 Step 3: Complete Product Suite & Downloads"
])


# =======================================================
# STEP 1: MARKET RESEARCH & STRUCTURED EXTRACTION
# =======================================================
with tab_step1:
    st.subheader("🔍 Step 1: Market Intelligence & Niche Discovery")
    st.caption("Enter a broad topic. AI will identify 3 profitable sub-niches with monetization potential.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        broad_topic = st.text_input("Enter Broad Niche / Target Audience", "Productivity & Deep Work for Remote Founders & Freelancers")
    with col_s2:
        platform_choice = st.selectbox("Primary Marketplace", ["Gumroad", "Etsy", "Amazon KDP", "Direct Web Store"])

    if st.button("🚀 Analyze & Discover Winning Sub-Niches", key="btn_run_research"):
        with st.spinner("AI market trends aur monetization opportunities calculate kar raha hai..."):
            try:
                prompt = f"""
                You are a world-class digital product strategist and market researcher.
                Analyze the market for: '{broad_topic}' targeted on '{platform_choice}'.
                
                Identify EXACTLY 3 highly profitable SUB-NICHES.
                
                FIRST, provide a detailed, actionable market overview report with audience pain points, winning angles, and monetization advice.
                
                SECOND, at the very end of your response, output a structured JSON block enclosed in '=== JSON_START ===' and '=== JSON_END ===' with the exact schema:
                === JSON_START ===
                {{
                  "sub_niches": [
                    {{
                      "name": "Sub-Niche 1 Exact Name",
                      "title": "High-Converting E-Book Title 1",
                      "subtitle": "Compelling Subtitle and Promise 1",
                      "price": "$19 - $29"
                    }},
                    {{
                      "name": "Sub-Niche 2 Exact Name",
                      "title": "High-Converting E-Book Title 2",
                      "subtitle": "Compelling Subtitle and Promise 2",
                      "price": "$24 - $37"
                    }},
                    {{
                      "name": "Sub-Niche 3 Exact Name",
                      "title": "High-Converting E-Book Title 3",
                      "subtitle": "Compelling Subtitle and Promise 3",
                      "price": "$29 - $49"
                    }}
                  ]
                }}
                === JSON_END ===
                """
                raw_research_text, used_m = generate_with_retry(prompt, model_choice, available_models)
                clean_rep, extracted_sn = parse_research_and_niches(raw_research_text)
                
                st.session_state.research_report = clean_rep
                st.session_state.extracted_niches = extracted_sn
                st.success(f"Market Research Complete! 3 Sub-Niches extracted. (Engine: `{used_m}`)")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.research_report:
        st.markdown(st.session_state.research_report)
        st.info("👉 Ab **Step 2: Auto-Extract & Configure** tab par jayein. Teeno options auto-populate ho chuki hain!")


# =======================================================
# STEP 2: AUTO-EXTRACT, SELECT & CONFIGURE
# =======================================================
with tab_step2:
    st.subheader("🎯 Step 2: Select Sub-Niche Option")
    st.caption("Research se 3 options nikal li gayi hain. Neeche aik option choose karein — sab kuch automatically fill ho jayega!")

    options_list = [f"🎯 Sub-Niche {i+1}: {sn['name']}" for i, sn in enumerate(st.session_state.extracted_niches)]
    selected_idx = st.selectbox("Select One Winning Sub-Niche to Build:", range(len(options_list)), format_func=lambda x: options_list[x])

    chosen_sn = st.session_state.extracted_niches[selected_idx]

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        chosen_niche = st.text_input("Selected Sub-Niche / Core Angle (Auto-Filled)", value=chosen_sn.get("name", ""))
        p_title = st.text_input("Digital Product Main Title (Auto-Filled)", value=chosen_sn.get("title", ""))
        p_subtitle = st.text_input("Subtitle / Hook (Auto-Filled)", value=chosen_sn.get("subtitle", ""))
    with col_c2:
        p_author = st.text_input("Brand / Author Name", value="OmniCraft Publishing")
        p_price = st.text_input("Target Selling Price (Auto-Filled)", value=chosen_sn.get("price", "$19 - $29"))
        num_chapters = st.slider("E-Book Chapter Count", 2, 4, 3)

    st.markdown("---")
    st.markdown("### 🛠️ Complete Assets Package to Build:")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.checkbox("📄 1. Master E-Book (Print-Ready PDF with Cover & Chapters)", value=True, disabled=True)
        st.checkbox("🗓️ 2. Aesthetic Printable Planner (Structured Time-Blocks & Goals PDF)", value=True, disabled=True)
    with col_a2:
        st.checkbox("💻 3. Interactive Web App / Calculator (Self-Contained HTML/JS)", value=True, disabled=True)
        st.checkbox("🎨 4. Canva Marketing Blueprints & Direct Canvas Links", value=True, disabled=True)
        st.checkbox("📝 5. Gumroad/Etsy High-Converting Sales Listing Copy", value=True, disabled=True)

    if st.button("⚡ Generate Complete Digital Product Suite (1-Click Launch Kit)", key="btn_build_all"):
        with st.spinner(f"🚀 AI '{p_title}' ke liye poori Digital Product Suite build kar raha hai..."):
            try:
                # 1. Master Call 1: Generate E-Book Content
                ebook_prompt = f"""
                You are an award-winning author. Write a high-value, comprehensive {num_chapters}-chapter guide titled '{p_title}'.
                Subtitle: '{p_subtitle}'. Target Niche: '{chosen_niche}'.
                
                FORMAT STRICTLY AS:
                ### CHAPTER 1: [Title]
                [Detailed practical paragraphs with action steps]
                > Pro Tip: [A powerful key takeaway quote]
                
                ### CHAPTER 2: [Title]
                [Content]
                
                (Continue for all {num_chapters} chapters without missing anything.)
                """
                raw_ebook_text, _ = generate_with_retry(ebook_prompt, model_choice, available_models)
                
                # Parse Chapters safely
                chapters_list = parse_ebook_chapters(raw_ebook_text)
                ebook_pdf_bytes = build_pro_ebook(p_title, p_author, p_subtitle, chapters_list)

                # 2. Compile Planner Data
                planner_goals = [
                    f"Complete core deep work block for {chosen_niche}",
                    "Audit and eliminate top 3 digital distractions",
                    "Review daily output metrics and log achievements"
                ]
                planner_sched = [
                    ("08:00 - 10:00 AM", "Deep Focus: Core High-Leverage Execution"),
                    ("10:00 - 11:30 AM", "Creative Sprint & Project Development"),
                    ("11:30 - 12:30 PM", "Strategic Communications & Review"),
                    ("01:30 - 03:00 PM", "Task Batching & Operational Admin"),
                    ("03:00 - 04:30 PM", "Skill Growth & Deep Learning Block"),
                    ("05:00 - 06:00 PM", "Daily Wrap-up, Next Day Goal Setting")
                ]
                planner_notes = f"Small daily disciplines compound into massive long-term freedom in {chosen_niche}."
                planner_pdf_bytes = build_pro_planner(f"{p_title} Planner", p_author, planner_goals, planner_sched, planner_notes)

                # 2-second safe cooldown to protect RPM rate limits
                time.sleep(2)

                # 3. Master Call 2: Generate Code Tool + Canva + Sales Copy Together
                bundle_prompt = f"""
                You are a senior digital product engineer and conversion copywriter.
                For the product: '{p_title}' in niche: '{chosen_niche}' priced at '{p_price}':

                Generate THREE distinct assets separated by exact delimiter tags:

                === WEB_APP_START ===
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{p_title}</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; padding: 30px; display: flex; justify-content: center; }}
                        .app-card {{ background: #1e293b; border-radius: 12px; padding: 25px; max-width: 600px; width: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.3); border: 1px solid #334155; }}
                        h2 {{ color: #818cf8; margin-top: 0; }}
                        .btn {{ background: #4f46e5; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 15px; }}
                        .btn:hover {{ background: #4338ca; }}
                        input, select {{ width: 100%; padding: 10px; margin: 8px 0; background: #0f172a; border: 1px solid #475569; color: white; border-radius: 6px; box-sizing: border-box; }}
                        .result-box {{ background: #0f172a; border-left: 4px solid #818cf8; padding: 15px; margin-top: 20px; border-radius: 4px; display: none; }}
                    </style>
                </head>
                <body>
                    <div class="app-card">
                        <h2>⚡ {p_title} — Interactive Tool</h2>
                        <p style="color: #94a3b8;">Tailored execution tool for {chosen_niche}</p>
                        <label>Enter Daily Work Hours:</label>
                        <input type="number" id="hours" value="6">
                        <label>Target Hourly Income Goal ($):</label>
                        <input type="number" id="rate" value="50">
                        <button class="btn" onclick="calculate()">🚀 Calculate Monthly Projected Output</button>
                        <div id="result" class="result-box"></div>
                    </div>
                    <script>
                        function calculate() {{
                            let h = parseFloat(document.getElementById('hours').value) || 0;
                            let r = parseFloat(document.getElementById('rate').value) || 0;
                            let monthly = h * r * 22;
                            let res = document.getElementById('result');
                            res.style.display = 'block';
                            res.innerHTML = "<b>Monthly Potential:</b> $" + monthly.toLocaleString() + "<br/><b>Yearly Revenue:</b> $" + (monthly * 12).toLocaleString() + "<br/><i>Focus on high-value output to scale this number.</i>";
                        }}
                    </script>
                </body>
                </html>
                === WEB_APP_END ===

                === CANVA_START ===
                ### 🎨 Canva Marketing Blueprint for {p_title}
                - **Hex Palette:** `#0f172a` (Background), `#4f46e5` (Primary Brand), `#06b6d4` (Accent), `#f8fafc` (Text)
                - **Typography:** `Montserrat Bold` (Headline) + `Lato Regular` (Body)
                - **Instagram Carousel Hook:** "Stop doing 8 hours of busywork. Here's how to finish your work in 3 hours."
                - **Pinterest Pin Title:** "{p_title} (Free Downloadable Guide & Planner)"
                - **Canva Element Keywords:** 'dark minimal gradient', 'productivity chart line', 'focus neon blob'
                === CANVA_END ===

                === SALES_COPY_START ===
                # 🚀 {p_title}
                ### *{p_subtitle}*

                **Are you exhausted from endless digital noise and unstructured work days?**
                This complete execution toolkit gives you the exact framework to take back control, double your deep work efficiency, and hit your revenue goals in {chosen_niche}.

                ### 📦 What You Get Inside:
                - ✅ **The Master Framework E-Book (PDF)**: Step-by-step actionable guide.
                - ✅ **Printable Daily Execution Planner (PDF)**: Printable time-blocking sheet.
                - ✅ **Interactive Output Calculator (Web App)**: Custom browser tool.
                - ✅ **Canva Marketing Templates**: High-CTR promotional assets.

                **Regular Price:** ~~$59~~ | **Today's Launch Special:** **{p_price}**
                === SALES_COPY_END ===
                """
                raw_bundle_text, _ = generate_with_retry(bundle_prompt, model_choice, available_models)

                # Parse Multi-Asset Outputs safely
                code_html, canva_blueprint, sales_copy = parse_bundle_response(raw_bundle_text)

                # Save all to session state
                st.session_state.bundle_data = {
                    "title": p_title,
                    "author": p_author,
                    "ebook_pdf": ebook_pdf_bytes,
                    "planner_pdf": planner_pdf_bytes,
                    "code_html": code_html,
                    "canva_blueprint": canva_blueprint,
                    "sales_copy": sales_copy
                }
                st.success("🎉 Complete Product Suite Tayyar Hai! Check Step 3 tab.")
                
            except Exception as e:
                st.error(f"Error during generation: {e}")


# =======================================================
# STEP 3: DOWNLOAD & LAUNCH CENTER
# =======================================================
with tab_step3:
    st.subheader("📦 Step 3: Complete Product Suite & Download Hub")
    
    if not st.session_state.bundle_data:
        st.info("ℹ️ Pehle **Step 1** mein research karein aur **Step 2** se product generate karein.")
    else:
        b = st.session_state.bundle_data
        
        st.markdown(f"### 🚀 Launch Bundle: **{b['title']}**")
        st.caption(f"Brand: {b['author']} | All assets packaged and ready to sell.")
        
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("#### 📖 1. Master E-Book (PDF)")
            st.write("Complete multi-chapter guide with custom cover page, headers, and formatted typography.")
            st.download_button(
                label="📥 Download Ready E-Book (PDF)",
                data=b["ebook_pdf"],
                file_name=f"{b['title'].replace(' ', '_').lower()}_ebook.pdf",
                mime="application/pdf"
            )
            
            st.markdown("---")
            st.markdown("#### 🗓️ 2. Printable Daily Planner (PDF)")
            st.write("Aesthetic daily execution planner with zero overlapping, priority grids & reflection blocks.")
            st.download_button(
                label="📥 Download Printable Planner (PDF)",
                data=b["planner_pdf"],
                file_name=f"{b['title'].replace(' ', '_').lower()}_planner.pdf",
                mime="application/pdf"
            )

        with col_d2:
            st.markdown("#### 💻 3. Interactive Web App / Tool (HTML)")
            st.write("Self-contained interactive software tool with modern UI.")
            st.download_button(
                label="📥 Download Interactive Web App (.html)",
                data=b["code_html"],
                file_name=f"{b['title'].replace(' ', '_').lower()}_tool.html",
                mime="text/html"
            )
            
            st.markdown("---")
            st.markdown("#### 🎨 4. Canva Free Studio Links")
            st.markdown("👉 [Open Canva Instagram Post Canvas](https://www.canva.com/create/instagram-posts/)")
            st.markdown("👉 [Open Canva Pinterest Pin Canvas](https://www.canva.com/create/pinterest-pins/)")
            st.markdown("👉 [Open Canva E-Book Cover Canvas](https://www.canva.com/create/book-covers/)")

        st.markdown("---")
        with st.expander("🎨 View Canva Marketing Blueprint & Prompts"):
            st.markdown(b["canva_blueprint"])

        with st.expander("📝 View High-Converting Sales Copy & Description"):
            st.markdown(b["sales_copy"])

        with st.expander("💻 Live Preview of Generated Interactive Web Tool"):
            st.components.v1.html(b["code_html"], height=550, scrolling=True)


# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "⚡ Built with Gemini Pro & Streamlit | Automated Digital Product Studio"
    "</div>",
    unsafe_allow_html=True
)
