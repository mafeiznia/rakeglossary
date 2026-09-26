"""Generate a RakeGlossary .ico icon.

Run once from the project root:
    python desktop/assets/make_icon.py

Output:
    desktop/assets/icon.ico  (multi-size 16/32/48/64/128/256)
    desktop/assets/icon.png  (256x256 preview)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- Config ---
OUT_DIR = Path(__file__).resolve().parent
BG_TOP = (99, 102, 241)      # indigo-500  #6366F1
BG_BOTTOM = (67, 56, 202)    # indigo-700  #4338CA
FG = (255, 255, 255)         # white
TEXT = "RG"
SIZE = 256

# --- Helpers ---
def _linear_gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    """Return a vertical linear gradient image."""
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / max(size - 1, 1)
        r = round(top[0] * (1 - t) + bottom[0] * t)
        g = round(top[1] * (1 - t) + bottom[1] * t)
        b = round(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    return grad.resize((size, size))


def _rounded_mask(size: int, radius: int) -> Image.Image:
    """Return a soft-cornered mask (L mode)."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=radius, fill=255
    )
    return mask


def _find_font(px: int) -> ImageFont.FreeTypeFont:
    """Try to load a nice bold sans font at the requested pixel size."""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
        "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
        "C:/Windows/Fonts/calibrib.ttf",   # Calibri Bold
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    return ImageFont.load_default()


# --- Main ---
def build_icon() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Gradient background
    bg = _linear_gradient(SIZE, BG_TOP, BG_BOTTOM)

    # 2) Rounded-rectangle mask
    mask = _rounded_mask(SIZE, radius=48)

    # 3) Compose RGBA
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img.paste(bg, (0, 0), mask)

    # 4) Draw text centered
    draw = ImageDraw.Draw(img)
    font = _find_font(px=128)
    bbox = draw.textbbox((0, 0), TEXT, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - tw) // 2 - bbox[0]
    y = (SIZE - th) // 2 - bbox[1] - 6  # slight optical adjustment
    draw.text((x, y), TEXT, font=font, fill=FG)

    # 5) Save as PNG (preview)
    png_path = OUT_DIR / "icon.png"
    img.save(png_path, "PNG")
    print(f"[ok] wrote {png_path}")

    # 6) Save as multi-size .ico
    ico_path = OUT_DIR / "icon.ico"
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=sizes)
    print(f"[ok] wrote {ico_path}")

    # 7) Also produce a small PNG for docs/README
    small_png = OUT_DIR / "icon-64.png"
    img.resize((64, 64), Image.LANCZOS).save(small_png, "PNG")
    print(f"[ok] wrote {small_png}")


if __name__ == "__main__":
    build_icon()