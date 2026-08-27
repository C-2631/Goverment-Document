import os
import io
import random
import pypdf
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "DLR_parichist_5_draft.pdf")
if not os.path.exists(TEMPLATE_PATH):
    replica_template = os.path.join(BASE_DIR, "templates", "DLR_parichist_5_replica.pdf")
    if os.path.exists(replica_template):
        TEMPLATE_PATH = replica_template

if os.getenv("VERCEL"):
    OUTPUT_DIR = "/tmp"
else:
    OUTPUT_DIR = os.path.join(BASE_DIR, "fileld_pdfs")
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
except Exception:
    OUTPUT_DIR = "/tmp"
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
DEFAULT_SIGN_PATH = os.path.join(BASE_DIR, "signatures", "sign.png")

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Register Noto Sans Gujarati fonts
REGULAR_FONT_PATH = os.path.join(FONTS_DIR, "NotoSansGujarati-Regular.ttf")
BOLD_FONT_PATH = os.path.join(FONTS_DIR, "NotoSansGujarati-Bold.ttf")

if os.path.exists(REGULAR_FONT_PATH):
    pdfmetrics.registerFont(TTFont("NotoSansGujarati", REGULAR_FONT_PATH))
    print("Registered NotoSansGujarati font.")
else:
    print(f"Warning: Regular font not found at {REGULAR_FONT_PATH}, falling back to Helvetica")

if os.path.exists(BOLD_FONT_PATH):
    pdfmetrics.registerFont(TTFont("NotoSansGujarati-Bold", BOLD_FONT_PATH))
    print("Registered NotoSansGujarati-Bold font.")
else:
    print(f"Warning: Bold font not found at {BOLD_FONT_PATH}, falling back to Helvetica-Bold")

# X, Y coordinate mappings for PDF overlay
# Coordinates calibrated for the new clean replica template (DLR_parichist_5_draft.pdf) v4
COORDINATES = {
    # Top-right applicant block
    "applicant_name": (330, 780, "NotoSansGujarati", 11),
    "address_line1": (330, 758, "NotoSansGujarati", 10),
    "address_line2": (330, 736, "NotoSansGujarati", 10),
    "address_line3": (330, 715, "NotoSansGujarati", 10),
    "mobile": (330, 712, "NotoSansGujarati", 10),
    "date": (330, 688, "NotoSansGujarati", 10),

    # Top-left recipient block
    "to_officer": (42, 688, "NotoSansGujarati", 10),
    "officer_district": (42, 675, "NotoSansGujarati", 10),
    "office_village": (65, 653, "NotoSansGujarati", 10),

    # Subject fields (વિષય)
    "subject_moje": (200, 622, "NotoSansGujarati", 9),
    "subject_taluko": (360, 622, "NotoSansGujarati", 9),
    "subject_jillo": (150, 602, "NotoSansGujarati", 9),
    "subject_survey_no": (305, 602, "NotoSansGujarati", 9),

    # Body text fields
    "body_name": (230, 532, "NotoSansGujarati", 10),
    "body_moje": (220, 510, "NotoSansGujarati", 9),
    "body_taluko": (390, 510, "NotoSansGujarati", 9),
    "body_jillo": (95, 488, "NotoSansGujarati", 9),
    "body_survey_no": (285, 488, "NotoSansGujarati", 9),
    "copy_details": (170, 466, "NotoSansGujarati", 9),
    "copy_quantity": (320, 466, "NotoSansGujarati", 10),

    # Bottom verification fields
    "mtr_no": (120, 317, "NotoSansGujarati", 10),
    "online_app_no": (190, 295, "NotoSansGujarati", 10),
    "surveyor_name": (185, 273, "NotoSansGujarati", 10),
    "measurement_date": (450, 273, "NotoSansGujarati", 10),

    # Other options
    "deposit_fee": (260, 223, "NotoSansGujarati", 10),
    "behalf_name": (315, 179, "NotoSansGujarati", 10),
}

# ---------------------------------------------------------------------------
# PRE-DEFINED SIGNATURE / HEADER TEXT
# These hardcoded values are printed on every generated PDF regardless of
# chatbot input.  They override the dynamic applicant & officer fields.
# ---------------------------------------------------------------------------

# Fixed random 10-digit mobile number (seeded so it is the same across restarts)
PREDEFINED_MOBILE = str(random.Random(42).randint(6000000000, 9999999999))

# Format: field_key -> (text_value, x, y, font_name, font_size)
PREDEFINED_FIELDS = {
    # Applicant block (top-right of form)
    "applicant_name": ("GAJRAJSINH KHERADIYA", 330, 780, "Helvetica-Bold", 11),
    "address_line1":  ('102 "PRATIK", 20/25,', 330, 758, "Helvetica-Bold", 10),
    "address_line2":  ("NEW JAGNATH PLOT, RAJKOT, 360001", 330, 736, "Helvetica-Bold", 9),
    "mobile":         (PREDEFINED_MOBILE, 330, 712, "Helvetica-Bold", 10),
    # "date" is intentionally left blank

    # Officer block (left side of form)
    "to_officer":       ("LAND RECORD INSPECTOR", 42, 688, "Helvetica-Bold", 10),
    "officer_district": ("RAJKOT", 42, 675, "Helvetica-Bold", 10),
    "office_village":   ("RAJKOT", 65, 653, "Helvetica-Bold", 10),
}

# Fields to skip in the dynamic (chatbot) rendering loop.
# Includes all predefined fields plus address_line3 (unused for predefined address).
PREDEFINED_FIELD_KEYS = set(PREDEFINED_FIELDS.keys()) | {"address_line3"}

def get_font_name(font_alias: str) -> str:
    """Fall back to Helvetica if Noto Sans Gujarati is not registered."""
    if font_alias == "NotoSansGujarati" and not os.path.exists(REGULAR_FONT_PATH):
        return "Helvetica"
    if font_alias == "NotoSansGujarati-Bold" and not os.path.exists(BOLD_FONT_PATH):
        return "Helvetica-Bold"
    return font_alias

def split_address(address: str) -> tuple:
    """Helper to split a multi-line address string into three parts for formatting."""
    if not address:
        return "", "", ""
    
    # Split by explicit newlines
    parts = [p.strip() for p in address.split("\n") if p.strip()]
    if len(parts) == 1:
        # Split by comma if only one line
        parts = [p.strip() for p in address.split(",") if p.strip()]
        
    while len(parts) < 3:
        parts.append("")
        
    # Join excess parts into the third line if needed
    if len(parts) > 3:
        parts[2] = ", ".join(parts[2:])
        parts = parts[:3]
        
    return parts[0], parts[1], parts[2]

def generate_pdf(session_id: str, data: dict) -> str:
    """
    Overlays form data and the pre-defined signature on the template PDF.
    Returns the path to the generated PDF.
    """
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template PDF not found at {TEMPLATE_PATH}")

    # Prepare data dictionary including split address
    flat_data = data.copy()
    a1, a2, a3 = split_address(data.get("address", ""))
    flat_data["address_line1"] = a1
    flat_data["address_line2"] = a2
    flat_data["address_line3"] = a3

    # If body_name is empty, default it to the applicant_name
    if not flat_data.get("body_name") and flat_data.get("applicant_name"):
        flat_data["body_name"] = flat_data["applicant_name"]
        
    # If body fields are empty, copy from subject fields
    for field in ["moje", "taluko", "jillo", "survey_no"]:
        subj_val = flat_data.get(f"subject_{field}", "")
        if subj_val and not flat_data.get(f"body_{field}"):
            flat_data[f"body_{field}"] = subj_val

    # Create PDF canvas in memory
    packet = io.BytesIO()
    # A4 size in points: 595.28 x 841.89
    can = canvas.Canvas(packet, pagesize=(595.28, 841.89))

    # ----- Pre-defined signature text (bold, hardcoded) -----
    for key, (text, x, y, font_name, size) in PREDEFINED_FIELDS.items():
        can.setFont(font_name, size)
        can.drawString(x, y, text)

    # ----- Dynamic text fields (chatbot-collected data) -----
    for key, (x, y, font_alias, size) in COORDINATES.items():
        if key in PREDEFINED_FIELD_KEYS:
            continue  # Skip — already drawn by predefined block above
        val = flat_data.get(key, "")
        if val is None:
            val = ""
        val_str = str(val).strip()
        if val_str:
            font_name = get_font_name(font_alias)
            can.setFont(font_name, size)
            can.drawString(x, y, val_str)

    # Place signature (pre-defined permanent signature)
    sig_path = data.get("signature_path") or DEFAULT_SIGN_PATH
    if sig_path and os.path.exists(sig_path):
        # Position at the "આપનો વિશ્વાસુ (સહી)" right side area
        # X ~ 420, Y ~ 330, width=100, height=45
        can.drawImage(sig_path, 420, 330, width=100, height=45, mask='auto')
    else:
        print(f"Warning: Signature file not found at {sig_path}")

    can.save()
    packet.seek(0)

    # Read original PDF and merge
    new_pdf = pypdf.PdfReader(packet)
    existing_pdf = pypdf.PdfReader(TEMPLATE_PATH)
    
    writer = pypdf.PdfWriter()
    
    # Merge the overlay onto the first page
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    writer.add_page(page)

    # Save output
    output_filename = f"filled_{session_id}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
