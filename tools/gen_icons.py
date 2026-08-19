"""tools/gen_icons.py — Generate clean PNG icon set for BILLSzuka PDFs.

Replaces emojis with minimalist line/fill icons. Consistent 64×64 base, transparent BG.
Output: data/_icons/*.png

Icon catalog:
  - Boolean: check.png, cross.png
  - Confidence (5 colors): dot-5.png (green) ... dot-1.png (red)
  - Flags (6): flag-check.png (✓ verified), flag-warn.png (⚠), flag-whale.png (🐋 big),
               flag-red.png (🔴 alert), flag-green.png (🟢 active), flag-diamond.png (💎 premium)
"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "data" / "_icons"
OUT.mkdir(parents=True, exist_ok=True)

# Palette (locked blue/grey + status colors only)
BLUE_DARK = (38, 50, 70)
GREY_DARK = (90, 90, 90)
GREY_MID = (150, 150, 150)
GREY_LIGHT = (210, 210, 210)
WHITE = (255, 255, 255)

# Status colors (5-level confidence + 3 priority)
GREEN = (52, 168, 83)     # dot-5 verified
YELLOW = (251, 188, 5)    # dot-4 likely
ORANGE = (255, 142, 56)   # dot-3 estimate
GRAY = (160, 160, 160)    # dot-2 unknown
RED = (217, 48, 48)       # dot-1 weak / flag-red

# Flags
FLAG_BLUE = (38, 50, 70)      # standard verified
FLAG_AMBER = (251, 188, 5)    # warning
FLAG_NAVY = (45, 80, 130)     # whale = big
FLAG_RED = (217, 48, 48)
FLAG_GREEN = (52, 168, 83)
FLAG_PURPLE = (130, 80, 170)  # diamond

SIZE = 64


def _new():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def _save(img: Image.Image, name: str) -> None:
    path = OUT / name
    img.save(path, "PNG")
    print(f"  → {path.relative_to(OUT.parent.parent)}")


# --- Boolean: check, cross ---
def make_check() -> None:
    img = _new()
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), outline=GREEN, width=4)
    # Tick
    d.line([(18, 34), (28, 44), (46, 22)], fill=GREEN, width=5)
    _save(img, "check.png")


def make_cross() -> None:
    img = _new()
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), outline=GREY_MID, width=4)
    # X
    d.line([(20, 20), (44, 44)], fill=GREY_DARK, width=5)
    d.line([(44, 20), (20, 44)], fill=GREY_DARK, width=5)
    _save(img, "cross.png")


# --- Confidence dots (5 colors) ---
def make_dot(color: tuple, name: str) -> None:
    img = _new()
    d = ImageDraw.Draw(img)
    d.ellipse((12, 12, 52, 52), fill=color)
    # subtle ring
    d.ellipse((12, 12, 52, 52), outline=(0, 0, 0, 60), width=1)
    _save(img, name)


# --- Flags (rectangular with pictogram inside) ---
def _flag_base(color: tuple) -> Image.Image:
    img = _new()
    d = ImageDraw.Draw(img)
    # rounded rect flag body
    d.rounded_rectangle((10, 8, 54, 56), radius=4, fill=color)
    return img


def make_flag_check() -> None:
    img = _flag_base(FLAG_BLUE)
    d = ImageDraw.Draw(img)
    d.line([(18, 34), (28, 44), (46, 22)], fill=WHITE, width=5)
    _save(img, "flag-check.png")


def make_flag_warn() -> None:
    img = _flag_base(FLAG_AMBER)
    d = ImageDraw.Draw(img)
    # Triangle
    d.polygon([(32, 18), (48, 46), (16, 46)], fill=WHITE)
    d.line([(32, 26), (32, 36)], fill=FLAG_AMBER, width=3)
    d.ellipse((30, 39, 34, 43), fill=FLAG_AMBER)
    _save(img, "flag-warn.png")


def make_flag_whale() -> None:
    """Big account = whale (stylized)."""
    img = _flag_base(FLAG_NAVY)
    d = ImageDraw.Draw(img)
    # Stylized whale tail: two arcs
    d.arc((14, 22, 50, 46), start=200, end=340, fill=WHITE, width=4)
    d.ellipse((18, 30, 30, 42), fill=WHITE)
    d.ellipse((40, 28, 52, 40), fill=WHITE)
    d.line([(46, 22), (50, 18), (54, 22)], fill=WHITE, width=3)
    _save(img, "flag-whale.png")


def make_flag_red() -> None:
    img = _flag_base(FLAG_RED)
    d = ImageDraw.Draw(img)
    d.ellipse((24, 22, 40, 38), fill=WHITE)
    d.ellipse((28, 26, 36, 34), fill=FLAG_RED)
    _save(img, "flag-red.png")


def make_flag_green() -> None:
    img = _flag_base(FLAG_GREEN)
    d = ImageDraw.Draw(img)
    d.line([(20, 32), (30, 42), (46, 24)], fill=WHITE, width=5)
    _save(img, "flag-green.png")


def make_flag_diamond() -> None:
    img = _flag_base(FLAG_PURPLE)
    d = ImageDraw.Draw(img)
    # Diamond shape
    d.polygon([(32, 16), (48, 32), (32, 48), (16, 32)], fill=WHITE)
    d.polygon([(32, 22), (42, 32), (32, 42), (22, 32)], fill=FLAG_PURPLE)
    _save(img, "flag-diamond.png")


def main() -> None:
    print("Generating BILLSzuka icon set → data/_icons/")
    make_check()
    make_cross()
    for color, name in [
        (GREEN, "dot-5.png"),
        (YELLOW, "dot-4.png"),
        (ORANGE, "dot-3.png"),
        (GRAY, "dot-2.png"),
        (RED, "dot-1.png"),
    ]:
        make_dot(color, name)
    make_flag_check()
    make_flag_warn()
    make_flag_whale()
    make_flag_red()
    make_flag_green()
    make_flag_diamond()
    print(f"Done: 14 icons in {OUT}")


if __name__ == "__main__":
    main()
