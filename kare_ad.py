#!/usr/bin/env python3
"""
KARE — Men's Hair Conditioner
Chemistry-focused ad presentation PDF generator.

Usage:
    python kare_ad.py
    python kare_ad.py --output my-file.pdf
"""

import argparse
import os
import sys
import tempfile
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate,
        Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether, Image,
    )
    from reportlab.pdfgen import canvas as pdfgen_canvas
except ImportError:
    print("Error: reportlab required.  pip install reportlab")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─── Brand palette ────────────────────────────────────────────────────────────
BEIGE_DARK   = colors.HexColor("#B89A6A")   # primary brand beige
BEIGE_MID    = colors.HexColor("#D4BA8E")   # secondary
BEIGE_LIGHT  = colors.HexColor("#EDE3D1")   # backgrounds
BEIGE_PALE   = colors.HexColor("#FAF7F2")   # page tint
CHARCOAL     = colors.HexColor("#1C1C1C")   # body text
WARM_WHITE   = colors.HexColor("#FEFCF8")
GOLD_ACCENT  = colors.HexColor("#8B6437")
TAUPE        = colors.HexColor("#6B5C47")

PAGE_W = 8.5 * inch
PAGE_H = 11.0 * inch
MARGIN = 0.75 * inch
BODY_W = PAGE_W - 2 * MARGIN

# ─── Fonts (built-ins only — no TTF dependency) ───────────────────────────────
H_FONT  = "Helvetica-Bold"
B_FONT  = "Helvetica"
BI_FONT = "Helvetica-Oblique"

TEMP_FILES = []


def _tmp_png():
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    TEMP_FILES.append(path)
    return path


# ─── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_brand": ps("cover_brand",
            fontName=H_FONT, fontSize=52, textColor=WARM_WHITE,
            alignment=TA_CENTER, leading=56, spaceAfter=4),
        "cover_tagline": ps("cover_tagline",
            fontName=BI_FONT, fontSize=14, textColor=BEIGE_LIGHT,
            alignment=TA_CENTER, leading=20, spaceAfter=6),
        "cover_sub": ps("cover_sub",
            fontName=B_FONT, fontSize=10, textColor=BEIGE_MID,
            alignment=TA_CENTER, leading=14),
        "section_head": ps("section_head",
            fontName=H_FONT, fontSize=16, textColor=GOLD_ACCENT,
            spaceBefore=18, spaceAfter=6, leading=20),
        "molecule_label": ps("molecule_label",
            fontName=H_FONT, fontSize=11, textColor=CHARCOAL,
            spaceBefore=10, spaceAfter=2, leading=14),
        "body": ps("body",
            fontName=B_FONT, fontSize=10, textColor=CHARCOAL,
            leading=15, spaceAfter=4),
        "body_italic": ps("body_italic",
            fontName=BI_FONT, fontSize=10, textColor=TAUPE,
            leading=14, spaceAfter=3),
        "caption": ps("caption",
            fontName=BI_FONT, fontSize=8, textColor=TAUPE,
            alignment=TA_CENTER, spaceBefore=2, spaceAfter=8),
        "callout": ps("callout",
            fontName=H_FONT, fontSize=12, textColor=GOLD_ACCENT,
            alignment=TA_CENTER, leading=16, spaceBefore=4, spaceAfter=4),
        "footer": ps("footer",
            fontName=B_FONT, fontSize=7, textColor=BEIGE_MID,
            alignment=TA_CENTER),
        "bullet": ps("bullet",
            fontName=B_FONT, fontSize=10, textColor=CHARCOAL,
            leading=15, leftIndent=14, spaceAfter=3),
    }


# ─── Page canvas callbacks ─────────────────────────────────────────────────────
class KareCanvas:
    def __init__(self, is_cover=False):
        self.is_cover = is_cover

    def __call__(self, canv, doc):
        canv.saveState()
        w, h = letter

        if doc.page == 1:
            # Dark full-bleed cover background
            canv.setFillColor(CHARCOAL)
            canv.rect(0, 0, w, h, fill=1, stroke=0)

            # Beige diagonal stripe (decorative)
            canv.setFillColor(BEIGE_DARK)
            canv.setStrokeColor(BEIGE_DARK)
            p = canv.beginPath()
            p.moveTo(0, h * 0.38)
            p.lineTo(w, h * 0.28)
            p.lineTo(w, h * 0.32)
            p.lineTo(0, h * 0.43)
            p.close()
            canv.drawPath(p, fill=1, stroke=0)

            # Subtle bottom bar
            canv.setFillColor(BEIGE_DARK)
            canv.rect(0, 0, w, 0.55 * inch, fill=1, stroke=0)

            # Bottom bar text
            canv.setFont(B_FONT, 8)
            canv.setFillColor(CHARCOAL)
            canv.drawCentredString(
                w / 2, 0.2 * inch,
                "KARE — Precision Chemistry for Men's Hair"
            )
        else:
            # Interior pages: pale beige background + thin top rule
            canv.setFillColor(BEIGE_PALE)
            canv.rect(0, 0, w, h, fill=1, stroke=0)

            canv.setStrokeColor(BEIGE_DARK)
            canv.setLineWidth(2)
            canv.line(MARGIN, h - 0.45 * inch, w - MARGIN, h - 0.45 * inch)

            # Running header
            canv.setFont(H_FONT, 8)
            canv.setFillColor(BEIGE_DARK)
            canv.drawString(MARGIN, h - 0.35 * inch, "KARE")
            canv.setFont(B_FONT, 8)
            canv.setFillColor(TAUPE)
            canv.drawRightString(
                w - MARGIN, h - 0.35 * inch,
                "The Chemistry of Exceptional Hair"
            )

            # Footer rule + page number
            canv.setStrokeColor(BEIGE_MID)
            canv.setLineWidth(0.5)
            canv.line(MARGIN, 0.55 * inch, w - MARGIN, 0.55 * inch)
            canv.setFont(B_FONT, 7)
            canv.setFillColor(TAUPE)
            canv.drawCentredString(w / 2, 0.3 * inch, f"— {doc.page} —")

        canv.restoreState()


# ─── Matplotlib helpers ────────────────────────────────────────────────────────
def ingredient_bar_chart():
    """Horizontal benefit bars for 5 key ingredients."""
    if not HAS_MPL:
        return None

    ingredients = [
        "Cetrimonium Chloride",
        "Hydrolyzed Keratin",
        "Panthenol (Vit B5)",
        "Cetyl Alcohol",
        "Argan Oil",
    ]
    benefits = {
        "Smoothing": [92, 55, 70, 88, 75],
        "Moisture":  [45, 60, 95, 65, 80],
        "Repair":    [50, 90, 70, 40, 65],
    }
    b_colors = ["#C9AA7C", "#8B6437", "#1C1C1C"]
    x = range(len(ingredients))
    bar_h = 0.22
    offsets = [-bar_h, 0, bar_h]

    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    fig.patch.set_facecolor("#FAF7F2")
    ax.set_facecolor("#FAF7F2")

    for i, (label, vals) in enumerate(benefits.items()):
        positions = [xi + offsets[i] for xi in x]
        bars = ax.barh(positions, vals, height=bar_h * 0.85,
                       color=b_colors[i], label=label, alpha=0.9)

    ax.set_yticks(list(x))
    ax.set_yticklabels(ingredients, fontsize=8)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Efficacy Index", fontsize=8, color="#6B5C47")
    ax.tick_params(axis="x", labelsize=7, colors="#6B5C47")
    ax.tick_params(axis="y", labelsize=8, colors="#1C1C1C")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D4BA8E")
    ax.spines["bottom"].set_color("#D4BA8E")
    ax.xaxis.label.set_color("#6B5C47")
    legend = ax.legend(fontsize=7, framealpha=0.6, loc="lower right")
    legend.get_frame().set_facecolor("#FAF7F2")

    ax.set_title("Ingredient Efficacy Profile", fontsize=9,
                 color="#8B6437", fontweight="bold", pad=6)

    path = _tmp_png()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def ph_arc_chart():
    """Donut showing pH position of KARE vs shampoo vs harsh alkaline."""
    if not HAS_MPL:
        return None

    fig, ax = plt.subplots(figsize=(3.2, 2.4), subplot_kw={"aspect": "equal"})
    fig.patch.set_facecolor("#FAF7F2")

    labels  = ["Hair\n(pH 4.5–5.5)", "KARE\nConditioner\n(pH 4.5)", "Shampoo\n(pH 6–7)", "Alkaline\n(pH 8+)"]
    sizes   = [25, 25, 25, 25]
    c_list  = ["#C9AA7C", "#8B6437", "#6B5C47", "#1C1C1C"]
    explode = [0, 0.12, 0, 0]

    wedges, texts = ax.pie(
        sizes, labels=labels, colors=c_list, explode=explode,
        startangle=90, wedgeprops={"width": 0.45, "edgecolor": "#FAF7F2", "linewidth": 1.5},
        textprops={"fontsize": 6.5, "color": "#1C1C1C"},
    )
    ax.text(0, 0, "pH\nScale", ha="center", va="center",
            fontsize=8, fontweight="bold", color="#8B6437")
    ax.set_title("pH Alignment", fontsize=8, color="#8B6437",
                 fontweight="bold", pad=4)

    path = _tmp_png()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def hair_structure_diagram():
    """Simple visual of cuticle layers with KARE action arrows."""
    if not HAS_MPL:
        return None

    fig, ax = plt.subplots(figsize=(4.2, 2.2))
    fig.patch.set_facecolor("#FAF7F2")
    ax.set_facecolor("#FAF7F2")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    # Hair shaft cross-section (simplified ellipse)
    from matplotlib.patches import Ellipse, FancyArrowPatch

    ellipse_outer = Ellipse((3.5, 2), width=2.4, height=3.2,
                             angle=0, facecolor="#B89A6A", edgecolor="#8B6437",
                             linewidth=1.5, alpha=0.85)
    ellipse_cortex = Ellipse((3.5, 2), width=1.6, height=2.2,
                              angle=0, facecolor="#D4BA8E", edgecolor="#B89A6A",
                              linewidth=1, alpha=0.9)
    ellipse_medulla = Ellipse((3.5, 2), width=0.6, height=0.8,
                               angle=0, facecolor="#EDE3D1", edgecolor="#D4BA8E",
                               linewidth=0.8, alpha=0.9)
    ax.add_patch(ellipse_outer)
    ax.add_patch(ellipse_cortex)
    ax.add_patch(ellipse_medulla)

    # Labels
    ax.text(3.5, 3.7, "Cuticle", ha="center", va="center",
            fontsize=7, color="#8B6437", fontweight="bold")
    ax.text(3.5, 2.0, "Cortex", ha="center", va="center",
            fontsize=6.5, color="#6B5C47")
    ax.text(3.5, 2.0, "\nMedulla", ha="center", va="center",
            fontsize=5.5, color="#B89A6A")

    # Action annotations on right side
    actions = [
        (5.8, 3.4, "#8B6437", "Cetrimonium Cl⁻/Cl⁺\nseals cuticle"),
        (5.8, 2.4, "#8B6437", "Keratin peptides\nfill cortex gaps"),
        (5.8, 1.4, "#8B6437", "Panthenol\npenetrates & hydrates"),
        (5.8, 0.5, "#8B6437", "Cetyl alcohol\nsmooths surface"),
    ]
    for x, y, col, txt in actions:
        ax.annotate(txt, xy=(4.8, y), xytext=(x, y),
                    fontsize=6, color="#1C1C1C",
                    arrowprops=dict(arrowstyle="->", color=col,
                                   lw=0.8, connectionstyle="arc3,rad=0.1"),
                    va="center")

    ax.set_title("How KARE Works — Inside the Hair Shaft", fontsize=8,
                 color="#8B6437", fontweight="bold", pad=4)

    path = _tmp_png()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─── Callout box ──────────────────────────────────────────────────────────────
def callout_box(text, label="KEY FACT", styles=None):
    """Returns a KeepTogether block styled as a highlighted callout."""
    inner_style = ParagraphStyle(
        "CalloutInner", fontName=B_FONT, fontSize=10,
        textColor=CHARCOAL, leading=15, alignment=TA_CENTER,
    )
    label_style = ParagraphStyle(
        "CalloutLabel", fontName=H_FONT, fontSize=8,
        textColor=GOLD_ACCENT, leading=10, alignment=TA_CENTER,
        spaceAfter=3,
    )
    tbl = Table(
        [[Paragraph(label, label_style)],
         [Paragraph(text, inner_style)]],
        colWidths=[BODY_W - 0.5 * inch],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BEIGE_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 1.5, BEIGE_DARK),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (0, 0),    8),
        ("TOPPADDING",    (0, 1), (0, 1),    4),
        ("BOTTOMPADDING", (0, -1), (0, -1), 10),
    ]))
    return KeepTogether([Spacer(1, 8), tbl, Spacer(1, 10)])


# ─── Ingredient card row ───────────────────────────────────────────────────────
def ingredient_card(number, name, chem, function, benefit, styles):
    num_style = ParagraphStyle(
        "NumStyle", fontName=H_FONT, fontSize=18,
        textColor=BEIGE_DARK, alignment=TA_CENTER, leading=22,
    )
    name_style = ParagraphStyle(
        "IngName", fontName=H_FONT, fontSize=11,
        textColor=CHARCOAL, leading=14, spaceAfter=1,
    )
    chem_style = ParagraphStyle(
        "IngChem", fontName=BI_FONT, fontSize=8,
        textColor=TAUPE, leading=10, spaceAfter=3,
    )
    body_s = ParagraphStyle(
        "IngBody", fontName=B_FONT, fontSize=9,
        textColor=CHARCOAL, leading=13,
    )

    left_cell = Paragraph(number, num_style)
    right_cell = [
        Paragraph(name, name_style),
        Paragraph(chem, chem_style),
        Paragraph(f"<b>Function:</b> {function}", body_s),
        Paragraph(f"<b>Benefit:</b> {benefit}", body_s),
    ]

    tbl = Table(
        [[left_cell, right_cell]],
        colWidths=[0.55 * inch, BODY_W - 0.55 * inch],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BACKGROUND",    (0, 0), (-1, -1), WARM_WHITE),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BEIGE_MID),
        ("BOX",           (0, 0), (-1, -1), 0.5, BEIGE_MID),
        ("LEFTPADDING",   (0, 0), (0, 0),   0),
        ("BACKGROUND",    (0, 0), (0, 0),   BEIGE_LIGHT),
    ]))
    return KeepTogether([tbl, Spacer(1, 6)])


# ─── Main builder ─────────────────────────────────────────────────────────────
def build_pdf(output_path: str):
    S = make_styles()
    cb = KareCanvas()

    doc = BaseDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=0.9 * inch,
        bottomMargin=0.75 * inch,
    )

    # Cover frame (full bleed — no top margin offset)
    cover_frame = Frame(
        0, 0, PAGE_W, PAGE_H,
        leftPadding=MARGIN, rightPadding=MARGIN,
        topPadding=2.8 * inch, bottomPadding=0.7 * inch,
    )
    body_frame = Frame(
        MARGIN, 0.7 * inch,
        BODY_W, PAGE_H - 1.5 * inch,
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
    )

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cb),
        PageTemplate(id="body",  frames=[body_frame],  onPage=cb),
    ])

    elements = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    from reportlab.platypus import NextPageTemplate, PageBreak

    elements.append(NextPageTemplate("cover"))
    elements.append(Spacer(1, 0.6 * inch))
    elements.append(Paragraph("KARE", S["cover_brand"]))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(HRFlowable(
        width="60%", thickness=1.5, color=BEIGE_DARK, hAlign="CENTER"))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        "The Chemistry of Exceptional Hair", S["cover_tagline"]))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(
        "Men's Advanced Conditioning Formula", S["cover_sub"]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Precision-engineered. Science-backed. Built for men.", S["cover_sub"]))

    # ── PAGE 2 — THE SCIENCE OF HAIR ──────────────────────────────────────────
    elements.append(NextPageTemplate("body"))
    elements.append(PageBreak())

    elements.append(Paragraph("The Science of Men's Hair", S["section_head"]))
    elements.append(Paragraph(
        "Hair is not just a fiber — it is a complex biological structure with three "
        "distinct layers, each requiring targeted chemistry to remain healthy, strong, "
        "and resilient under daily stress.", S["body"]))

    elements.append(Spacer(1, 8))

    # Hair structure diagram
    diagram_path = hair_structure_diagram()
    if diagram_path:
        img = Image(diagram_path, width=4.2 * inch, height=2.2 * inch)
        elements.append(img)
        elements.append(Paragraph(
            "Fig 1 — Cross-section of a hair shaft showing KARE's active ingredient delivery zones.",
            S["caption"]))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Most men's hair faces a specific combination of challenges:", S["body"]))

    challenges = [
        ("Mechanical stress", "daily styling, combing, environmental friction strip the cuticle"),
        ("Sebum build-up", "active scalp glands leave heavy residue that clogs follicles"),
        ("Protein loss", "heat, UV, and hard water leach keratin from the cortex"),
        ("Dehydration", "razor-short styles expose more scalp surface to moisture loss"),
    ]
    for title, desc in challenges:
        elements.append(Paragraph(
            f"• <b>{title}</b> — {desc}.", S["bullet"]))

    elements.append(Spacer(1, 10))
    elements.append(callout_box(
        "Human hair carries a <b>net negative charge</b> when wet. "
        "KARE's positively charged actives are drawn to the hair surface "
        "like a magnet — sealing the cuticle precisely where it needs protection.",
        label="THE ELECTROSTATIC PRINCIPLE",
    ))

    # ── PAGE 3 — KEY INGREDIENTS ───────────────────────────────────────────────
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BEIGE_MID))
    elements.append(Paragraph("Key Ingredients &amp; Their Chemistry", S["section_head"]))
    elements.append(Paragraph(
        "Five precision-selected actives, each with a specific molecular role "
        "in the conditioning matrix:", S["body"]))
    elements.append(Spacer(1, 8))

    ingredients = [
        (
            "01",
            "Cetrimonium Chloride",
            "C₁₉H₄₂ClN — Quaternary Ammonium Salt",
            "Cationic surfactant that adsorbs electrostatically onto the anionic hair surface. "
            "Forms a thin, uniform monolayer that reduces friction between strands.",
            "Instant detangling, reduced static, defined style without weight.",
        ),
        (
            "02",
            "Hydrolyzed Keratin",
            "Protein fragments (MW 1,000–10,000 Da)",
            "Low-molecular-weight keratin peptides that penetrate the cortex through the "
            "cuticle pores. They cross-link with internal disulfide bonds to reinforce "
            "weakened hair architecture.",
            "Visibly repaired, stronger hair with up to 40% less breakage.",
        ),
        (
            "03",
            "Panthenol (Pro-Vitamin B₅)",
            "C₉H₁₉NO₄ — Pantothenic acid alcohol",
            "A powerful humectant that binds up to three times its weight in water. "
            "Converted to pantothenic acid inside the cortex where it integrates into "
            "the hair's own moisture reservoir.",
            "All-day hydration, improved elasticity, and natural shine.",
        ),
        (
            "04",
            "Cetyl Alcohol",
            "C₁₆H₃₄O — Long-chain fatty alcohol",
            "Acts as both emollient and emulsifier. Creates a smooth, lubricating film "
            "over the cuticle surface and stabilises the water-oil emulsion in the formula "
            "so active compounds remain evenly distributed.",
            "Silky texture in hand; smooth, manageable hair after rinsing.",
        ),
        (
            "05",
            "Argan Oil (Argania spinosa kernel oil)",
            "Rich in oleic acid (C18:1), linoleic acid (C18:2), and α-tocopherol (Vit E)",
            "Lipophilic fatty acids permeate the hydrophobic cortex and fill micro-fractures "
            "caused by heat and UV exposure. Vitamin E neutralises free radicals that "
            "degrade the hair's disulfide bond network.",
            "Restored lustre, UV protection, and long-term structural resilience.",
        ),
    ]

    for args in ingredients:
        elements.append(ingredient_card(*args, styles=S))

    # ── PAGE 4 — EFFICACY + pH SCIENCE ────────────────────────────────────────
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BEIGE_MID))
    elements.append(Paragraph("Ingredient Efficacy Profile", S["section_head"]))

    bar_path = ingredient_bar_chart()
    if bar_path:
        img = Image(bar_path, width=min(6.5 * inch, BODY_W), height=2.8 * inch)
        elements.append(img)
        elements.append(Paragraph(
            "Fig 2 — Comparative efficacy index for Smoothing, Moisture retention, "
            "and Repair across KARE's five active ingredients.",
            S["caption"]))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("The pH Advantage", S["section_head"]))
    elements.append(Paragraph(
        "pH is the most overlooked variable in hair care chemistry. "
        "KARE is formulated at <b>pH 4.5</b> — precisely matching the "
        "natural isoelectric point of healthy hair. This tight alignment "
        "triggers the cuticle to close flat, maximising shine and "
        "minimising porosity after every wash.", S["body"]))

    elements.append(Spacer(1, 6))

    ph_path = ph_arc_chart()
    if ph_path:
        col1 = Image(ph_path, width=3.0 * inch, height=2.4 * inch)
        col2_content = [
            Paragraph("pH Effects on the Cuticle", S["molecule_label"]),
            Paragraph(
                "At <b>pH 4–5</b> (KARE): cuticle scales lie flat, "
                "reflecting light uniformly → high shine, low porosity.", S["body"]),
            Spacer(1, 4),
            Paragraph(
                "At <b>pH 6–7</b> (standard shampoo): cuticle partially "
                "lifts, surface becomes rough → dull, frizzy appearance.", S["body"]),
            Spacer(1, 4),
            Paragraph(
                "At <b>pH 8+</b> (alkaline): cuticle fully opens, cortex "
                "exposed to protein leaching and mechanical damage.", S["body"]),
        ]
        layout = Table(
            [[col1, col2_content]],
            colWidths=[3.2 * inch, BODY_W - 3.2 * inch],
        )
        layout.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(layout)
        elements.append(Paragraph(
            "Fig 3 — pH zones relative to KARE's target formulation point.",
            S["caption"]))

    # ── PAGE 5 — HOW TO USE + CLOSING ─────────────────────────────────────────
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BEIGE_MID))
    elements.append(Paragraph("How to Use KARE", S["section_head"]))

    steps = [
        ("Cleanse", "Wash with a sulphate-mild shampoo (pH 5.5–6) to avoid alkaline shock."),
        ("Apply",   "Dispense a coin-sized amount and distribute through damp hair, "
                    "avoiding the scalp — let the cationics bind where damage is highest."),
        ("Dwell",   "Leave on for 2–3 minutes. Panthenol requires time to cross the "
                    "cuticle barrier and saturate the cortex."),
        ("Rinse",   "Rinse with cool water to encourage cuticle closure and seal the "
                    "conditioning layer in place."),
    ]

    step_style = ParagraphStyle(
        "StepNum", fontName=H_FONT, fontSize=20,
        textColor=BEIGE_DARK, alignment=TA_CENTER, leading=24,
    )
    step_title = ParagraphStyle(
        "StepTitle", fontName=H_FONT, fontSize=10,
        textColor=CHARCOAL, leading=13, spaceAfter=2,
    )
    step_body = ParagraphStyle(
        "StepBody", fontName=B_FONT, fontSize=9,
        textColor=CHARCOAL, leading=13,
    )

    step_rows = []
    for i, (title, desc) in enumerate(steps, 1):
        num_cell  = Paragraph(str(i), step_style)
        text_cell = [
            Paragraph(title, step_title),
            Paragraph(desc, step_body),
        ]
        step_rows.append([num_cell, text_cell])

    step_tbl = Table(step_rows,
                     colWidths=[0.55 * inch, BODY_W - 0.55 * inch])
    step_tbl.setStyle(TableStyle([
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1),  0),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0,0), (-1, -1), 8),
        ("BACKGROUND",  (0, 0), (-1, -1), WARM_WHITE),
        ("BACKGROUND",  (0, 0), (0, -1),  BEIGE_LIGHT),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.5, BEIGE_MID),
        ("BOX",         (0, 0), (-1, -1), 0.5, BEIGE_MID),
    ]))
    elements.append(step_tbl)

    elements.append(Spacer(1, 16))
    elements.append(callout_box(
        "KARE is not skincare imitating haircare.<br/>"
        "It is <b>hair chemistry, perfected for men.</b>",
        label="OUR PROMISE",
    ))

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1, color=BEIGE_DARK))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"KARE — Men's Advanced Hair Conditioning  |  "
        f"Science Edition  |  {datetime.now().strftime('%Y')}",
        S["footer"],
    ))

    # ── BUILD ──────────────────────────────────────────────────────────────────
    doc.build(elements)

    for f in TEMP_FILES:
        try:
            os.unlink(f)
        except OSError:
            pass

    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate KARE ad presentation PDF")
    parser.add_argument("--output", "-o", default="kare-ad.pdf",
                        help="Output PDF path (default: kare-ad.pdf)")
    args = parser.parse_args()

    print("Building KARE chemistry ad PDF...")
    out = build_pdf(args.output)
    print(f"Done → {out}")


if __name__ == "__main__":
    main()
