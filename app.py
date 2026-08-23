import streamlit as st
import google.generativeai as genai
import io
import time
import re
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
        if self._pageNumber > 1: # Suppress header/footer on Cover Page
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(40, letter - 30, "OFFICIAL DIGITAL PRODUCT SUITE")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, letter - 35, letter[0] - 40, letter - 35)

            # Footer
            self.drawRightString(letter[0] - 40, 25, f"Page {self._pageNumber} of {page_count}")
            self.drawString(40, 25, "Confidential & Exclusive Content | All Rights Reserved")
            self.line(40, 36, letter[0] - 40, 36)
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


# --- PREMIUM PLANNER PDF ENGINE (Zero Overlap & Clean Grid) ---
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

    # Table cell paragraph styles (crucial for zero text overlapping)
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


# --- STRICT TEXT-ONLY MODEL FILTER (Excludes Audio/TTS/Embedding Models) ---
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


# --- ROBUST GEMINI CALL (With Auto-Retry on 429) ---
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
    <span class="badge">END-TO-END PIPELINE</span>
    <h2>⚡ OmniCraft Studio — Full Digital Product Builder</h2>
    <p style="color: #94a3b8; margin-bottom: 0;">
        Research any niche, select a winning angle, and automatically generate a complete <b>Ready-to-Sell Product Bundle</b> (PDFs, Planners, Web Tools, Canva Assets & Sales Copy).
    </p>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.warning("⚠️ Baraye mehrbani Sidebar mein apni **Gemini API Key** enter karein.")
    st.stop()


# --- SESSION STATE MANAGEMENT ---
if "research_results" not in st.session_state:
    st.session_state.research_results = None
if "bundle_data" not in st.session_state:
    st.session_state.bundle_data = None


# --- WORKFLOW TABS ---
tab_step1, tab_step2, tab_step3 = st.tabs([
    "🔍 Step 1: Market Research",
    "🎯 Step 2: Choose Niche & Configure",
    "📦 Step 3: Complete Product Suite & Downloads"
])


# =======================================================
# STEP 1: MARKET RESEARCH & OPPORTUNITY DISCOVERY
# =======================================================
with tab_step1:
    st.subheader("🔍 Step 1: Market Intelligence & Niche Discovery")
    st.caption("Enter a broad topic. AI will identify 3 highly profitable sub-niches with monetization potential.")
    
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
                
                Identify EXACTLY 3 highly profitable SUB-NICHES. For each sub-niche, provide:
                - Sub-Niche Name
                - Core Target Customer & Burning Pain Point
                - Proposed E-Book / Guide Title
                - Proposed Printable Planner / Tracker Concept
                - Proposed Interactive Code / Calculator Web App Concept
                - Suggested Pricing ($9 - $49)
                
                Format with clear markdown headings and bullet points so the user can easily choose one.
                """
                research_text, used_m = generate_with_retry(prompt, model_choice, available_models)
                st.session_state.research_results = research_text
                st.success(f"Market Research Complete! (Engine: `{used_m}`)")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.research_results:
        st.markdown(st.session_state.research_results)
        st.info("👉 Ab **Step 2: Choose Niche & Configure** tab par jayein aur apna product bundle configure karein.")


# =======================================================
# STEP 2: CHOOSE NICHE & CONFIGURE LAUNCH SUITE
# =======================================================
with tab_step2:
    st.subheader("🎯 Step 2: Select Sub-Niche & Product Details")
    st.caption("Specify your exact product name and brand details based on the research above.")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        chosen_niche = st.text_input("Selected Sub-Niche / Core Angle", "Burnout Recovery & Deep Work Mastery for Freelancers")
        p_title = st.text_input("Digital Product Main Title", "UNSTOPPABLE FOCUS: The Freelancer's Deep Work Blueprint")
        p_subtitle = st.text_input("Subtitle / Hook", "Eliminate Digital Distractions, Build Consistent Daily Output & Double Revenue")
    with col_c2:
        p_author = st.text_input("Brand / Author Name", "OmniCraft Publishing")
        p_price = st.text_input("Target Selling Price", "$19 - $29")
        num_chapters = st.slider("E-Book Chapter Count", 2, 4, 3)

    st.markdown("---")
    st.markdown("### 🛠️ Assets to Build Automatically:")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.checkbox("📄 1. High-Value Master E-Book (Print-Ready PDF with Cover & Chapters)", value=True, disabled=True)
        st.checkbox("🗓️ 2. Aesthetic Printable Planner (Structured Time-Blocks & Goals PDF)", value=True, disabled=True)
    with col_a2:
        st.checkbox("💻 3. Interactive Web App / Calculator (Self-Contained HTML/JS)", value=True, disabled=True)
        st.checkbox("🎨 4. Canva Marketing Blueprints & Direct Canvas Links", value=True, disabled=True)
        st.checkbox("📝 5. Gumroad/Etsy High-Converting Sales Listing Copy", value=True, disabled=True)

    if st.button("⚡ Generate Complete Digital Product Suite (1-Click Launch Kit)", key="btn_build_all"):
        with st.spinner("🚀 AI poori Digital Product Suite build kar raha hai (Writing, Designing & Compiling PDFs)..."):
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
                
                # Parse Chapters (Fixed bug here)
                chapters_list = []
                for rc in raw_ebook_text.split("### CHAPTER "):
                    if not rc.strip():
                        continue
                    lines = rc.strip().split("\n", 1)
                    ch_h = "CHAPTER " + lines[0].strip()
                    ch_b = lines.strip() if len(lines) > 1 else ""
                    chapters_list.append((ch_h, ch_b))
                
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

                # Parse Multi-Asset Outputs
                code_html = ""
                canva_blueprint = ""
                sales_copy = ""

                if "=== WEB_APP_START ===" in raw_bundle_text and "=== WEB_APP_END ===" in raw_bundle_text:
                    code_html = raw_bundle_text.split("=== WEB_APP_START ===").split("=== WEB_APP_END ===")[0].strip()
                if "=== CANVA_START ===" in raw_bundle_text and "=== CANVA_END ===" in raw_bundle_text:
                    canva_blueprint = raw_bundle_text.split("=== CANVA_START ===").split("=== CANVA_END ===")[0].strip()
                if "=== SALES_COPY_START ===" in raw_bundle_text and "=== SALES_COPY_END ===" in raw_bundle_text:
                    sales_copy = raw_bundle_text.split("=== SALES_COPY_START ===").split("=== SALES_COPY_END ===")[0].strip()

                # Fallback if delimiter missed
                if not code_html:
                    code_html = "<h1>Interactive Tool Ready</h1>"

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
