"""Square-friendly before/after image (1200x1200) for the Project Catalog thumbnail."""
import csv
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
PDF = BASE / "data" / "sample_schedule.pdf"
CSV = BASE / "out" / "tables" / "page1_table1.csv"
OUT = BASE / "data" / "pdf_extraction_demo_square.png"

S = 1200
BG = (250, 250, 248)
MUTED = (120, 120, 120)
ACCENT = (11, 61, 58)
DARK = (22, 24, 26)

title_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 66)
sub_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
label_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 27)
mono_small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)

canvas = Image.new("RGB", (S, S), BG)
draw = ImageDraw.Draw(canvas)

draw.text((64, 46), "PDF in, Excel out", font=title_font, fill=ACCENT)
draw.text((66, 128), "headers and totals kept, one file per table", font=sub_font, fill=MUTED)

# --- PDF page, portrait, centred in the upper block
doc = pymupdf.open(PDF)
pix = doc[0].get_pixmap(dpi=130)
page = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

target_h = 400
scale = target_h / page.height
page = page.resize((int(page.width * scale), int(page.height * scale)), Image.LANCZOS)
px = (S - page.width) // 2
py = 190
canvas.paste(page, (px, py))
draw.rectangle([px, py, px + page.width, py + page.height], outline=(214, 214, 208), width=2)
draw.text((px, py + page.height + 12), "input.pdf", font=label_font, fill=MUTED)

# --- arrow
arrow_y = py + page.height + 46
draw.line([(S // 2, arrow_y), (S // 2, arrow_y + 46)], fill=ACCENT, width=4)
draw.polygon([(S // 2 - 12, arrow_y + 46), (S // 2 + 12, arrow_y + 46), (S // 2, arrow_y + 64)], fill=ACCENT)

# --- extracted table, dark panel
rows = list(csv.reader(CSV.open(encoding="utf-8")))
panel_x, panel_y = 70, arrow_y + 80
panel_w = S - 140
row_h = 44
panel_h = 74 + row_h * 6

draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                       radius=14, fill=DARK)
draw.text((panel_x + 30, panel_y + 22), "output.xlsx", font=mono_small, fill=(140, 200, 190))

cols = [0, 1, 2, 3, 4]
offsets = [30, 170, 620, 690, 830]
y = panel_y + 64
for r, row in enumerate(rows[:5]):
    x = panel_x
    colour = (150, 210, 200) if r == 0 else (235, 235, 230)
    for c in cols:
        if c >= len(row):
            continue
        text = row[c] if len(row[c]) <= 34 else row[c][:32] + "…"
        draw.text((x + offsets[c], y), text, font=mono_small if r == 0 else mono, fill=colour)
    y += row_h

canvas.save(OUT)
print(f"saved {OUT}")
