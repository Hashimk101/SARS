import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Initialize Presentation in 16:9 widescreen
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Theme Colors (Aerospace Dark HUD palette matching video)
BG_COLOR = RGBColor(11, 15, 25)        # #0B0F19 Deep space void
CARD_BG = RGBColor(17, 24, 39)         # #111827 Dark navy glass
CARD_BORDER = RGBColor(31, 41, 55)     # #1F2937 Subtle panel border
TEXT_WHITE = RGBColor(255, 255, 255)
TEXT_GRAY = RGBColor(148, 163, 184)    # #94A3B8 Slate
TEXT_MUTED = RGBColor(100, 116, 139)   # #64748B Dim gray
ORANGE = RGBColor(249, 115, 22)        # #F97316 Safety Orange
CYAN = RGBColor(56, 189, 248)          # #38BDF8 Electric Cyan
GREEN = RGBColor(16, 185, 129)         # #10B981 Emerald Green
PURPLE = RGBColor(168, 85, 247)        # #A855F7 Glacier Purple

FRAMES_DIR = "/home/hashim/.gemini/antigravity/brain/819f9727-5723-4858-b7b5-ad661cb47f96/scratch/video_analysis"

def add_header(slide, category_text, subcategory_text=""):
    """Adds consistent HUD header and mandatory AI disclosure watermark."""
    # Top Category
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(9.0), Inches(0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = category_text
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN
    
    if subcategory_text:
        run = p.add_run()
        run.text = f"  ·  {subcategory_text}"
        run.font.name = "Consolas"
        run.font.size = Pt(11)
        run.font.bold = False
        run.font.color.rgb = TEXT_GRAY

    # Watermark Top-Right
    tb_wm = slide.shapes.add_textbox(Inches(10.0), Inches(0.4), Inches(2.5), Inches(0.4))
    tf_wm = tb_wm.text_frame
    p_wm = tf_wm.paragraphs[0]
    p_wm.alignment = PP_ALIGN.RIGHT
    p_wm.text = "Made with AI assistance"
    p_wm.font.name = "Consolas"
    p_wm.font.size = Pt(10)
    p_wm.font.color.rgb = TEXT_MUTED

def set_slide_bg(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

# ==============================================================================
# SLIDE 1: Title Slide
# ==============================================================================
s1 = prs.slides.add_slide(blank_layout)
set_slide_bg(s1)
add_header(s1, "NASA INTERNATIONAL SPACE APPS CHALLENGE 2026", "CHALLENGE: DANCING WITH THE SARS")

# Title Box
tb_title = s1.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(2.0))
tf_title = tb_title.text_frame
p1 = tf_title.paragraphs[0]
r_sar = p1.add_run()
r_sar.text = "SAR"
r_sar.font.name = "Arial"
r_sar.font.size = Pt(56)
r_sar.font.bold = True
r_sar.font.color.rgb = TEXT_WHITE

r_pulse = p1.add_run()
r_pulse.text = "-Pulse"
r_pulse.font.name = "Arial"
r_pulse.font.size = Pt(56)
r_pulse.font.bold = True
r_pulse.font.color.rgb = ORANGE

p2 = tf_title.add_paragraph()
p2.text = "Dancing with the SARs: Earth Surface Dynamics & Radar Early Warning"
p2.font.name = "Arial"
p2.font.size = Pt(22)
p2.font.color.rgb = TEXT_GRAY

p3 = tf_title.add_paragraph()
p3.text = "Flagship Validation Study: Sinking City Quetta  ·  Pakistan National 4-Biome Radar Observatory"
p3.font.name = "Consolas"
p3.font.size = Pt(14)
p3.font.color.rgb = CYAN

# Hero Visual (Video frame showing call to action / UI overview)
img_s1 = os.path.join(FRAMES_DIR, "frame_28.jpg")
if os.path.exists(img_s1):
    s1.shapes.add_picture(img_s1, Inches(0.8), Inches(3.4), Inches(6.8), Inches(3.4))

# 3 Highlights Cards on Right
highlights = [
    ("🛰️ SPACE RADAR PHYSICS", "NISAR L-band & Sentinel-1 InSAR peer through clouds and soil to measure millimetric vertical displacement."),
    ("📉 THE QUETTA BOWL", "Valley sinking straight down at -8.7 cm/yr; 46 km² and 49k buildings sunk ≥1m by 2050 under current trend."),
    ("🌐 60fps SERVERLESS PLATFORM", "Pre-computed array science streamed in <25 KB payloads with Web Audio acoustic sonification.")
]

for idx, (title, desc) in enumerate(highlights):
    y_pos = Inches(3.4 + idx * 1.15)
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.8), y_pos, Inches(4.7), Inches(1.05))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    
    tb = s1.shapes.add_textbox(Inches(7.9), y_pos + Inches(0.05), Inches(4.5), Inches(0.95))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = "Arial"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ORANGE if idx == 1 else CYAN
    
    p_desc = tf.add_paragraph()
    p_desc.text = desc
    p_desc.font.name = "Arial"
    p_desc.font.size = Pt(10)
    p_desc.font.color.rgb = TEXT_WHITE

# ==============================================================================
# SLIDE 2: The Crisis — Quetta is Sinking (Video Scene 1)
# ==============================================================================
s2 = prs.slides.add_slide(blank_layout)
set_slide_bg(s2)
add_header(s2, "QUETTA · BALOCHISTAN · PAKISTAN", "30.18 N · 66.98 E · Arid High-Altitude Valley")

# Left Column: Video Frame 05 (Quetta terrain + building footprint)
img_s2 = os.path.join(FRAMES_DIR, "frame_05.jpg")
if os.path.exists(img_s2):
    s2.shapes.add_picture(img_s2, Inches(0.8), Inches(1.2), Inches(6.8), Inches(3.82))

# Left Bottom Note Card
c_note = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(6.8), Inches(1.8))
c_note.fill.solid()
c_note.fill.fore_color.rgb = CARD_BG
c_note.line.color.rgb = CARD_BORDER
tb_note = s2.shapes.add_textbox(Inches(0.9), Inches(5.3), Inches(6.6), Inches(1.6))
tf_n = tb_note.text_frame
tf_n.word_wrap = True
p = tf_n.paragraphs[0]
p.text = "THE OPTICAL SATELITTE BLIND SPOT:"
p.font.bold = True
p.font.size = Pt(11)
p.font.color.rgb = CYAN
p2 = tf_n.add_paragraph()
p2.text = "Standard optical satellites (Sentinel-2, Landsat) see only static arid ground color. They cannot detect sub-surface aquifer compaction, operate through dense monsoon storm clouds, or track millimetric structural strain."
p2.font.size = Pt(10)
p2.font.color.rgb = TEXT_WHITE

# Right Column Stat Cards
# Card 1: 2,000,000 People
c_pop = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(1.2), Inches(4.6), Inches(2.7))
c_pop.fill.solid()
c_pop.fill.fore_color.rgb = CARD_BG
c_pop.line.color.rgb = CARD_BORDER
tb_pop = s2.shapes.add_textbox(Inches(8.1), Inches(1.3), Inches(4.2), Inches(2.5))
tf_pop = tb_pop.text_frame
tf_pop.word_wrap = True
p = tf_pop.paragraphs[0]
p.text = "PEOPLE LIVE HERE"
p.font.name = "Consolas"
p.font.size = Pt(12)
p.font.color.rgb = TEXT_GRAY

p_num = tf_pop.add_paragraph()
p_num.text = "2,000,000+"
p_num.font.name = "Arial"
p_num.font.size = Pt(46)
p_num.font.bold = True
p_num.font.color.rgb = TEXT_WHITE

p_sub = tf_pop.add_paragraph()
p_sub.text = "more than two million residents in an arid closed basin"
p_sub.font.name = "Consolas"
p_sub.font.size = Pt(11)
p_sub.font.color.rgb = TEXT_GRAY

p_punch = tf_pop.add_paragraph()
p_punch.text = "...and the ground is sinking"
p_punch.font.name = "Arial"
p_punch.font.size = Pt(18)
p_punch.font.bold = True
p_punch.font.color.rgb = ORANGE

# Card 2: Root Causes
c_mech = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(4.1), Inches(4.6), Inches(2.9))
c_mech.fill.solid()
c_mech.fill.fore_color.rgb = CARD_BG
c_mech.line.color.rgb = CARD_BORDER
tb_mech = s2.shapes.add_textbox(Inches(8.1), Inches(4.2), Inches(4.2), Inches(2.7))
tf_m = tb_mech.text_frame
tf_m.word_wrap = True
p = tf_m.paragraphs[0]
p.text = "HYDROLOGIC DRIVERS OF COLLAPSE"
p.font.bold = True
p.font.size = Pt(12)
p.font.color.rgb = ORANGE

points = [
    ("Unregulated Over-Pumping:", "Deep tubewells for apple orchards and urban supply deplete the alluvial aquifer 300% faster than annual recharge."),
    ("Alluvial Bed Compaction:", "Pore water loss collapses lacustrine clay-silt layers, causing irreversible permanent surface drop."),
    ("Historical Sinking:", "Ground surveys & InSAR show up to 2.7 meters of cumulative subsidence since 2003.")
]
for title, body in points:
    p_pt = tf_m.add_paragraph()
    r1 = p_pt.add_run()
    r1.text = f"• {title} "
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = TEXT_WHITE
    r2 = p_pt.add_run()
    r2.text = body
    r2.font.size = Pt(10)
    r2.font.color.rgb = TEXT_GRAY

# ==============================================================================
# SLIDE 3: How NISAR Sees It — Orbital Radar (Video Scene 2)
# ==============================================================================
s3 = prs.slides.add_slide(blank_layout)
set_slide_bg(s3)
add_header(s3, "NISAR · L-BAND RADAR INTERFEROMETRY", "Jun–Oct 2026 · Track 41 Ascending + Track 92 Descending · 12-Day Cadence")

# Left Column: Video Frame 10 (InSAR deformation heatmap)
img_s3 = os.path.join(FRAMES_DIR, "frame_10.jpg")
if os.path.exists(img_s3):
    s3.shapes.add_picture(img_s3, Inches(0.8), Inches(1.2), Inches(6.8), Inches(3.82))

# Card under image: Vector Decomposition
c_vec = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(6.8), Inches(1.8))
c_vec.fill.solid()
c_vec.fill.fore_color.rgb = CARD_BG
c_vec.line.color.rgb = CARD_BORDER
tb_vec = s3.shapes.add_textbox(Inches(0.9), Inches(5.3), Inches(6.6), Inches(1.6))
tf_v = tb_vec.text_frame
tf_v.word_wrap = True
p = tf_v.paragraphs[0]
p.text = "2D VECTOR INVERSION (ASCENDING + DESCENDING):"
p.font.bold = True
p.font.size = Pt(11)
p.font.color.rgb = CYAN
p2 = tf_v.add_paragraph()
p2.text = "By combining NISAR Track 41 (Ascending LOS: -6.6 cm/yr) and Track 92 (Descending LOS: -7.3 cm/yr), we solve the full 2D displacement vector. East-west velocity inside the bowl is ~0.0 cm/yr: the entire valley floor is plunging straight down."
p2.font.size = Pt(10)
p2.font.color.rgb = TEXT_WHITE

# Right Column Stat Cards
# Card 1: -8.7 cm/yr Typical Sinking
c_rate = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(1.2), Inches(4.6), Inches(2.7))
c_rate.fill.solid()
c_rate.fill.fore_color.rgb = CARD_BG
c_rate.line.color.rgb = CARD_BORDER
tb_rate = s3.shapes.add_textbox(Inches(8.1), Inches(1.3), Inches(4.2), Inches(2.5))
tf_r = tb_rate.text_frame
tf_r.word_wrap = True
p = tf_r.paragraphs[0]
p.text = "TYPICAL SINKING · STRAIGHT DOWN"
p.font.name = "Consolas"
p.font.size = Pt(12)
p.font.color.rgb = TEXT_GRAY

p_num = tf_r.add_paragraph()
p_num.text = "-8.7 cm/yr"
p_num.font.name = "Arial"
p_num.font.size = Pt(46)
p_num.font.bold = True
p_num.font.color.rgb = ORANGE

p_sub = tf_r.add_paragraph()
p_sub.text = "median vertical velocity across the sinking bowl"
p_sub.font.name = "Consolas"
p_sub.font.size = Pt(11)
p_sub.font.color.rgb = TEXT_GRAY

p_dt = tf_r.add_paragraph()
p_dt.text = "City center sinks fastest: -14.8 cm/yr (annualized equivalent)"
p_dt.font.size = Pt(11)
p_dt.font.bold = True
p_dt.font.color.rgb = TEXT_WHITE

# Card 2: Ground Truth Validation r = 0.89
c_val = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(4.1), Inches(4.6), Inches(2.9))
c_val.fill.solid()
c_val.fill.fore_color.rgb = CARD_BG
c_val.line.color.rgb = CARD_BORDER
tb_val = s3.shapes.add_textbox(Inches(8.1), Inches(4.2), Inches(4.2), Inches(2.7))
tf_val = tb_val.text_frame
tf_val.word_wrap = True
p = tf_val.paragraphs[0]
p.text = "INDEPENDENT ESA SENTINEL-1 VALIDATION"
p.font.bold = True
p.font.size = Pt(12)
p.font.color.rgb = CYAN

p_val_num = tf_val.add_paragraph()
p_val_num.text = "r = 0.89"
p_val_num.font.name = "Arial"
p_val_num.font.size = Pt(36)
p_val_num.font.bold = True
p_val_num.font.color.rgb = TEXT_WHITE

p_val_desc = tf_val.add_paragraph()
p_val_desc.text = "Pixel-by-pixel cross-mission correlation against an independent 1-year ESA Sentinel-1 LiCSAR interferogram (Sep 2024–Sep 2025). NISAR L-band and Sentinel-1 C-band match across all 20,653 valley floor pixels."
p_val_desc.font.size = Pt(10)
p_val_desc.font.color.rgb = TEXT_GRAY

# ==============================================================================
# SLIDE 4: 2050 Probabilistic Scenarios (Video Scene 3)
# ==============================================================================
s4 = prs.slides.add_slide(blank_layout)
set_slide_bg(s4)
add_header(s4, "2050 SCENARIOS · NOT A FORECAST", "Median of 500 Monte Carlo Runs · NISAR Rate Annualized x0.75 · 124 km² Valley Floor")

# Left Column: Video Frame 22 (2050 cumulative bowl)
img_s4 = os.path.join(FRAMES_DIR, "frame_22.jpg")
if os.path.exists(img_s4):
    s4.shapes.add_picture(img_s4, Inches(0.8), Inches(1.2), Inches(6.8), Inches(3.82))

# Left Bottom Note: Damage Zones
c_dam = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.2), Inches(6.8), Inches(1.8))
c_dam.fill.solid()
c_dam.fill.fore_color.rgb = CARD_BG
c_dam.line.color.rgb = CARD_BORDER
tb_dam = s4.shapes.add_textbox(Inches(0.9), Inches(5.3), Inches(6.6), Inches(1.6))
tf_d = tb_dam.text_frame
tf_d.word_wrap = True
p = tf_d.paragraphs[0]
p.text = "GEOTECHNICAL DAMAGE MECHANISM (ANGULAR DISTORTION):"
p.font.bold = True
p.font.size = Pt(11)
p.font.color.rgb = ORANGE
p2 = tf_d.add_paragraph()
p2.text = "It is not uniform sinking that destroys buildings, but differential tilt (slope of subsidence surface). Where angular distortion exceeds Skempton-Bjerrum threshold (1/150), unreinforced masonry walls shear, pipelines rupture, and foundations crack."
p2.font.size = Pt(10)
p2.font.color.rgb = TEXT_WHITE

# Right Column Scenario Comparison
# S1 Card
c_s1 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(1.2), Inches(4.6), Inches(2.7))
c_s1.fill.solid()
c_s1.fill.fore_color.rgb = CARD_BG
c_s1.line.color.rgb = CARD_BORDER
tb_s1 = s4.shapes.add_textbox(Inches(8.1), Inches(1.3), Inches(4.2), Inches(2.5))
tf_s1 = tb_s1.text_frame
tf_s1.word_wrap = True
p = tf_s1.paragraphs[0]
p.text = "CURRENT TREND · STATUS QUO (S1)"
p.font.name = "Consolas"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = ORANGE

p_s1_stat = tf_s1.add_paragraph()
r_a = p_s1_stat.add_run()
r_a.text = "46 km²"
r_a.font.size = Pt(36)
r_a.font.bold = True
r_a.font.color.rgb = ORANGE

r_b = p_s1_stat.add_run()
r_b.text = "  ~49,000 buildings"
r_b.font.size = Pt(15)
r_b.font.bold = True
r_b.font.color.rgb = TEXT_WHITE

p_s1_det = tf_s1.add_paragraph()
p_s1_det.text = "• Sinks at least 1 meter deeper by 2050\n• 860,000 people exposed in heavy deformation zone\n• Core subsidence bowl exceeds 5.1 meters maximum drop"
p_s1_det.font.size = Pt(10)
p_s1_det.font.color.rgb = TEXT_GRAY

# S3 Card
c_s3 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(4.1), Inches(4.6), Inches(2.9))
c_s3.fill.solid()
c_s3.fill.fore_color.rgb = CARD_BG
c_s3.line.color.rgb = CARD_BORDER
tb_s3 = s4.shapes.add_textbox(Inches(8.1), Inches(4.2), Inches(4.2), Inches(2.7))
tf_s3 = tb_s3.text_frame
tf_s3.word_wrap = True
p = tf_s3.paragraphs[0]
p.text = "PUMPING CONTROLLED · POLICY INTERVENTION (S3)"
p.font.name = "Consolas"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = GREEN

p_s3_stat = tf_s3.add_paragraph()
r_c = p_s3_stat.add_run()
r_c.text = "6 km²"
r_c.font.size = Pt(36)
r_c.font.bold = True
r_c.font.color.rgb = GREEN

r_d = p_s3_stat.add_run()
r_d.text = "  ~7,300 buildings"
r_d.font.size = Pt(15)
r_d.font.bold = True
r_d.font.color.rgb = TEXT_WHITE

p_s3_det = tf_s3.add_paragraph()
p_s3_det.text = "• 87% reduction in submerged land area\n• 85% structural risk reduction (saving 41,700 buildings)\n• Managed aquifer recharge via 18 delay-action dams stabilizes the water table"
p_s3_det.font.size = Pt(10)
p_s3_det.font.color.rgb = TEXT_GRAY

# ==============================================================================
# SLIDE 5: The National Scope — 4 Pakistan Biomes
# ==============================================================================
s5 = prs.slides.add_slide(blank_layout)
set_slide_bg(s5)
add_header(s5, "NATIONAL RADAR OBSERVATORY · PAKISTAN", "4 Critical Biomes Mapped from Orbit with NISAR & Sentinel-1")

biomes = [
    ("INDUS RIVER BASIN", "26.85 N, 68.10 E", "🌊 MONSOON INUNDATION", CYAN,
     "• Physics: L-band HH double-bounce (> -5 dB) isolates submerged stems under dense storm clouds.\n• Impact: 14,200 km² flooded agricultural lands detected; 1.8M people protected via embankment monitoring."),
    
    ("QUETTA VALLEY", "30.18 N, 66.98 E", "🏙️ AQUIFER DESTRUCTION", ORANGE,
     "• Physics: Dual-orbit InSAR phase inversion reveals vertical lacustrine compaction.\n• Impact: -8.7 cm/yr typical sinking; 500-draw Monte Carlo 2050 simulation flags 49k endangered buildings."),
    
    ("MARGALLA HILLS", "33.73 N, 73.09 E", "🌲 CANOPY FRAGMENTATION", GREEN,
     "• Physics: HV cross-pol volume scattering drops by 10.6 dB on bulldozed hill plots (r² = 0.84 with biomass).\n• Impact: 35% Zone 3 native acacia scrub lost by 2030; +4.8°C urban heat island intensification."),
    
    ("SIACHEN GLACIERS", "35.42 N, 77.11 E", "🏔️ CRYOSPHERE SURGE & GLOF", PURPLE,
     "• Physics: Glaciological InSAR strain rate Regressor tracks velocity across debris-covered tongues.\n• Impact: 182 m/yr glacial slip; 14 unstable moraine dams screened for catastrophic outburst floods.")
]

card_w = Inches(5.6)
card_h = Inches(2.7)

for idx, (name, coords, phenomenon, color, desc) in enumerate(biomes):
    x = Inches(0.8) if idx % 2 == 0 else Inches(6.9)
    y = Inches(1.2) if idx < 2 else Inches(4.2)
    
    c = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
    c.fill.solid()
    c.fill.fore_color.rgb = CARD_BG
    c.line.color.rgb = color
    c.line.width = Pt(1.5)
    
    tb = s5.shapes.add_textbox(x + Inches(0.15), y + Inches(0.1), card_w - Inches(0.3), card_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = f"{phenomenon}  ·  {name}"
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = color
    
    p_c = tf.add_paragraph()
    p_c.text = coords
    p_c.font.name = "Consolas"
    p_c.font.size = Pt(10)
    p_c.font.color.rgb = TEXT_GRAY
    
    p_d = tf.add_paragraph()
    p_d.text = desc
    p_d.font.name = "Arial"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = TEXT_WHITE

# ==============================================================================
# SLIDE 6: The SAR-Pulse Interactive Platform (Video Scene 4)
# ==============================================================================
s6 = prs.slides.add_slide(blank_layout)
set_slide_bg(s6)
add_header(s6, "INTERACTIVE PROTOTYPE HUD · ARCHITECTURE", "Live Web Platform: https://sars-visualize.vercel.app/")

# Center Left: Video Frame 26 (The full prototype UI)
img_s6 = os.path.join(FRAMES_DIR, "frame_26.jpg")
if os.path.exists(img_s6):
    s6.shapes.add_picture(img_s6, Inches(0.8), Inches(1.2), Inches(7.5), Inches(4.22))

# Bottom Left Note
c_eng = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.6), Inches(7.5), Inches(1.4))
c_eng.fill.solid()
c_eng.fill.fore_color.rgb = CARD_BG
c_eng.line.color.rgb = CARD_BORDER
tb_eng = s6.shapes.add_textbox(Inches(0.9), Inches(5.65), Inches(7.3), Inches(1.3))
tf_e = tb_eng.text_frame
tf_e.word_wrap = True
p = tf_e.paragraphs[0]
p.text = "OFFLINE HEAVY SCIENCE + INSTANT 60fps WEB STREAMING"
p.font.bold = True
p.font.size = Pt(11)
p.font.color.rgb = CYAN
p2 = tf_e.add_paragraph()
p2.text = "Multi-gigabyte HDF5 arrays are pre-processed offline with spatial Lee filtering & InSAR vector inversion. Browser clients load sub-25 KB JSON and pre-rendered Cloud-Optimized GeoTIFFs with sub-second response times on any phone or laptop."
p2.font.size = Pt(9.5)
p2.font.color.rgb = TEXT_WHITE

# Right Column Features
features = [
    ("4-DOT NATIONAL MAP", "Clickable Pakistan tactical map toggling between Indus, Quetta, Islamabad, and Siachen dossiers.", CYAN),
    ("5-CHAPTER STORY DOSSIER", "Timeline → Human Pain Points → Physical Drivers → 2030 Tipping Point → Precautionary Action Plan.", ORANGE),
    ("DYNAMIC 2050 SLIDER", "Interactive year & policy scenario toggles backed by 500-draw Monte Carlo risk distributions.", GREEN),
    ("ACOUSTIC SONIFICATION", "Web Audio API maps radar backscatter curves into musical pitch and rhythm ('Dancing with the SARs').", PURPLE)
]

for idx, (title, desc, color) in enumerate(features):
    y = Inches(1.2 + idx * 1.45)
    c = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.5), y, Inches(4.0), Inches(1.35))
    c.fill.solid()
    c.fill.fore_color.rgb = CARD_BG
    c.line.color.rgb = CARD_BORDER
    
    tb = s6.shapes.add_textbox(Inches(8.6), y + Inches(0.08), Inches(3.8), Inches(1.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = "Arial"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = color
    
    p_d = tf.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(9.5)
    p_d.font.color.rgb = TEXT_GRAY

# ==============================================================================
# SLIDE 7: Action Plan & Galactic Impact (Video Scene 5)
# ==============================================================================
s7 = prs.slides.add_slide(blank_layout)
set_slide_bg(s7)
add_header(s7, "ACTION PLAN & GALACTIC IMPACT", "Space Apps Challenge 2026 · Best Use of Data, Science, and Impact")

# Hero Callout Box (Matching Video Closing)
c_hero = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.7), Inches(1.8))
c_hero.fill.solid()
c_hero.fill.fore_color.rgb = CARD_BG
c_hero.line.color.rgb = ORANGE
c_hero.line.width = Pt(2)

tb_hero = s7.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.3), Inches(1.6))
tf_h = tb_hero.text_frame
tf_h.word_wrap = True
p = tf_h.paragraphs[0]
r1 = p.add_run()
r1.text = "See the ground move. "
r1.font.name = "Arial"
r1.font.size = Pt(36)
r1.font.bold = True
r1.font.color.rgb = TEXT_WHITE

r2 = p.add_run()
r2.text = "Act in time."
r2.font.name = "Arial"
r2.font.size = Pt(36)
r2.font.bold = True
r2.font.color.rgb = ORANGE

p_sub = tf_h.add_paragraph()
p_sub.text = "From spaceborne radar physics to life-saving municipal intervention: turning raw gigabytes into community survival."
p_sub.font.name = "Arial"
p_sub.font.size = Pt(13)
p_sub.font.color.rgb = TEXT_GRAY

# 3 Action Pillars
pillars = [
    ("1. PUMPING CAPS", "ENFORCE TUBEWELL QUOTAS",
     "• Bi-weekly NISAR L-band delta tracking detects unauthorized industrial borehole clusters.\n• Enforce groundwater extraction caps through Balochistan Water Act with radar-backed legal proof.", ORANGE),
    
    ("2. ARTIFICIAL RECHARGE", "18 DELAY-ACTION DAMS",
     "• Construct managed retention structures in Hanna and Chiltan mountain catchments.\n• Captures 42M m³/year seasonal runoff, raising aquifer pore pressure and stabilizing the valley bowl.", CYAN),
    
    ("3. OPEN RADAR HUD", "COMMUNITY EARLY WARNING",
     "• Zero-login open web platform gives water managers, disaster response (NDMA), and residents free access.\n• Automated GeoJSON hazard boundary exports for urban planners & infrastructure engineers.", GREEN)
]

for idx, (pill, title, desc, col) in enumerate(pillars):
    x = Inches(0.8 + idx * 4.0)
    c = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.2), Inches(3.7), Inches(2.7))
    c.fill.solid()
    c.fill.fore_color.rgb = CARD_BG
    c.line.color.rgb = CARD_BORDER
    
    tb = s7.shapes.add_textbox(x + Inches(0.15), Inches(3.3), Inches(3.4), Inches(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = pill
    p.font.name = "Consolas"
    p.font.size = Pt(10)
    p.font.color.rgb = col
    
    p_t = tf.add_paragraph()
    p_t.text = title
    p_t.font.name = "Arial"
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE
    
    p_d = tf.add_paragraph()
    p_d.text = desc
    p_d.font.name = "Arial"
    p_d.font.size = Pt(10)
    p_d.font.color.rgb = TEXT_GRAY

# Footer Card with Links
c_foot = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.1), Inches(11.7), Inches(0.9))
c_foot.fill.solid()
c_foot.fill.fore_color.rgb = CARD_BG
c_foot.line.color.rgb = CARD_BORDER
tb_foot = s7.shapes.add_textbox(Inches(0.9), Inches(6.15), Inches(11.5), Inches(0.8))
tf_foot = tb_foot.text_frame
p = tf_foot.paragraphs[0]
p.text = "LIVE PLATFORM: https://sars-visualize.vercel.app/   |   API DOCS: /docs   |   REPO: github.com/Hashimk101/SARS"
p.font.name = "Consolas"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = CYAN

p_cred = tf_foot.add_paragraph()
p_cred.text = "Data Sources: NASA ASF DAAC · NASA-ISRO NISAR · ESA Copernicus Sentinel-1 · WorldPop · Microsoft Buildings"
p_cred.font.name = "Arial"
p_cred.font.size = Pt(9.5)
p_cred.font.color.rgb = TEXT_MUTED

# Save presentation to both root and docs/
output_path = "presentation.pptx"
docs_path = "docs/SAR-Pulse_NASA_Space_Apps_Presentation.pptx"
prs.save(output_path)
prs.save(docs_path)

print(f"Presentation successfully generated and saved to:")
print(f"  - {output_path}")
print(f"  - {docs_path}")
