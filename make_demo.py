"""Build a before/after image: PDF page on the left, extracted table on the right."""
import csv
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
PDF = BASE / "data" / "sample_schedule.pdf"
CSV = BASE / "out" / "tables" / "page1_table1.csv"
OUT = BASE / "data" / "pdf_extraction_demo.png"

W, H = 1800, 1000
BG = (250, 250, 248)
INK = (26, 26, 26)
MUTED = (120, 120, 120)
ACCENT = (11, 61, 58)

canvas = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(canvas)

title_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 40)
label_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24)
mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
small_mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)

draw.text((60, 40), "From PDF to a usable table", font=title_font, fill=ACCENT)
draw.text((60, 96), "one page in, one CSV per table out — headers intact, totals kept",
          font=label_font, fill=MUTED)

# left: the PDF page
doc = pymupdf.open(PDF)
pix = doc[0].get_pixmap(dpi=110)
page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
max_h = 760
scale = min(700 / page_img.width, max_h / page_img.height)
page_img = page_img.resize((int(page_img.width * scale), int(page_img.height * scale)), Image.LANCZOS)
canvas.paste(page_img, (70, 160))
draw.rectangle([70, 160, 70 + page_img.width, 160 + page_img.height], outline=(210, 210, 205), width=2)
draw.text((70, 930), "sample_schedule.pdf — page 1", font=label_font, fill=MUTED)

# right: the extracted CSV
rows = list(csv.reader(CSV.open(encoding="utf-8")))
box_x, box_y, box_w = 860, 160, 880
line_h = 38
box_h = 70 + line_h * (len(rows) + 1)

draw.rounded_rectangle([box_x, box_y, box_x + box_w, box_y + box_h], radius=10, fill=(22, 24, 26))
draw.text((box_x + 28, box_y + 20), "page1_table1.csv", font=small_mono, fill=(140, 200, 190))

y = box_y + 60
widths = [120, 330, 60, 120, 130]
for r, row in enumerate(rows[:12]):
    x = box_x + 28
    colour = (235, 235, 230) if r else (150, 210, 200)
    for c, cell in enumerate(row[:5]):
        text = cell if len(cell) <= 26 else cell[:24] + "…"
        draw.text((x, y), text, font=mono if r else small_mono, fill=colour)
        x += widths[c] if c < len(widths) else 120
    y += line_h

draw.text((box_x, box_y + box_h + 24), f"{len(rows) - 1} data rows · 5 columns · totals preserved",
          font=label_font, fill=MUTED)

canvas.save(OUT)
print(f"saved {OUT}")
