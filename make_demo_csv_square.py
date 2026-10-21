"""Square (1200x1200) before/after image for the CSV clean-up listing."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "data" / "csv_cleanup_demo_square.png"

S = 1200
BG = (250, 250, 248)
MUTED = (120, 120, 120)
ACCENT = (11, 61, 58)
DARK = (22, 24, 26)
CARD = (255, 255, 255)
BAD = (176, 58, 46)

title_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 62)
sub_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 29)
mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 24)
mono_small = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)

canvas = Image.new("RGB", (S, S), BG)
draw = ImageDraw.Draw(canvas)

draw.text((62, 44), "Messy CSV in, clean data out", font=title_font, fill=ACCENT)
draw.text((64, 124), "currency, dates, duplicates, bad rows - all handled", font=sub_font, fill=MUTED)

messy = [
    ("Date", "Customer", "Order Value"),
    ("31/01/2026", "Acme Ltd", "£1,234.50"),
    ("31/01/2026", "Acme Ltd", "£1,234.50"),
    ("2026-02-03", "Gamma", "1,000"),
    ("2026-13-01", "Delta", "call us"),
    ("01/02/2026", "Beta Co", "(210.00)"),
]

clean = [
    ("date", "customer", "order_value"),
    ("2026-01-31", "Acme Ltd", "1234.50"),
    ("2026-02-01", "Beta Co", "-210.00"),
    ("2026-02-03", "Gamma", "1000.00"),
]

# --- input card
cx, cy, cw = 62, 190, S - 124
ch = 74 + 40 * len(messy)
draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=14, fill=CARD, outline=(218, 218, 212), width=2)
draw.text((cx + 26, cy + 20), "export_january.csv", font=mono_small, fill=MUTED)

col = [26, 300, 700]
y = cy + 58
for r, row in enumerate(messy):
    for i, cell in enumerate(row):
        colour = MUTED if r == 0 else (BAD if r in (2, 3) else (40, 40, 40))
        draw.text((cx + col[i], y), cell, font=mono, fill=colour)
    if r == 2:
        draw.line([(cx + 20, y - 4), (cx + cw - 20, y - 4)], fill=(228, 190, 186), width=2)
    y += 40

# --- arrow
ay = cy + ch + 26
draw.line([(S // 2, ay), (S // 2, ay + 34)], fill=ACCENT, width=4)
draw.polygon([(S // 2 - 12, ay + 34), (S // 2 + 12, ay + 34), (S // 2, ay + 52)], fill=ACCENT)

# --- output card
oy = ay + 72
oh = 74 + 42 * len(clean)
draw.rounded_rectangle([cx, oy, cx + cw, oy + oh], radius=14, fill=DARK)
draw.text((cx + 26, oy + 20), "clean_january.csv", font=mono_small, fill=(140, 200, 190))

y = oy + 58
for r, row in enumerate(clean):
    for i, cell in enumerate(row):
        colour = (150, 210, 200) if r == 0 else (235, 235, 230)
        draw.text((cx + col[i], y), cell, font=mono_small if r == 0 else mono, fill=colour)
    y += 42

draw.text((cx, oy + oh + 22), "1 duplicate removed · 1 bad row flagged · formats standardised",
          font=sub_font, fill=MUTED)

canvas.save(OUT)
print(f"saved {OUT}")
