import io
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .qr import _build_logo, _gradient, BG_DARK, NEON_PURPLE, NEON_CYAN

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
VAZIR_BOLD = os.path.join(FONTS_DIR, "Vazirmatn-Bold.ttf")
VAZIR_MEDIUM = os.path.join(FONTS_DIR, "Vazirmatn-Medium.ttf")

SIZE = 1080
BG_MID = (24, 18, 58)
MUTED_TEXT = (185, 180, 210)


def _centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.FreeTypeFont, fill):
    bbox = font.getbbox(text, direction="rtl")
    w = bbox[2] - bbox[0]
    x = (SIZE - w) // 2 - bbox[0]
    draw.text((x, y), text, font=font, fill=fill, direction="rtl")
    return bbox[3] - bbox[1]


def _gradient_text(base: Image.Image, y: int, text: str, font: ImageFont.FreeTypeFont, c1, c2):
    bbox = font.getbbox(text, direction="rtl")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - w) // 2 - bbox[0]

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).text((x, y), text, font=font, fill=255, direction="rtl")
    grad = _gradient((SIZE, SIZE), c1, c2).convert("RGBA")
    base.paste(grad, (0, 0), mask)
    return h


def generate_promo_image(headline: str, price_line: str, subtitle: str, cta_text: str | None = None) -> io.BytesIO:
    """تصویر تبلیغاتی مربعی (۱۰۸۰x۱۰۸۰) برای پست تلگرام/اینستاگرام با هویت بصری NovaTunnel."""
    canvas = Image.new("RGB", (SIZE, SIZE), BG_DARK)
    grad_bg = _gradient((SIZE, SIZE), BG_DARK, BG_MID, horizontal=False)
    canvas.paste(grad_bg, (0, 0))

    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([-200, -200, 500, 500], fill=NEON_PURPLE + (70,))
    glow_draw.ellipse([SIZE - 500, SIZE - 500, SIZE + 200, SIZE + 200], fill=NEON_CYAN + (60,))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow)

    draw = ImageDraw.Draw(canvas)

    logo_w, logo_h = 460, 120
    logo = _build_logo(logo_w, logo_h)
    canvas.alpha_composite(logo, ((SIZE - logo_w) // 2, 90))

    headline_font = ImageFont.truetype(VAZIR_BOLD, 108)
    _gradient_text(canvas, 340, headline, headline_font, NEON_CYAN, NEON_PURPLE)

    price_font = ImageFont.truetype(VAZIR_BOLD, 64)
    _centered_text(draw, 500, price_line, price_font, (255, 255, 255))

    subtitle_font = ImageFont.truetype(VAZIR_MEDIUM, 38)
    _centered_text(draw, 620, subtitle, subtitle_font, MUTED_TEXT)

    if cta_text:
        pill_font = ImageFont.truetype(VAZIR_MEDIUM, 34)
        bbox = pill_font.getbbox(cta_text, direction="rtl")
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad_x, pad_y = 46, 26
        pill_w, pill_h = tw + pad_x * 2, th + pad_y * 2
        pill_x0 = (SIZE - pill_w) // 2
        pill_y0 = SIZE - 170
        border_mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(border_mask).rounded_rectangle(
            [pill_x0, pill_y0, pill_x0 + pill_w, pill_y0 + pill_h], radius=pill_h // 2, fill=255
        )
        grad_pill = _gradient((SIZE, SIZE), NEON_PURPLE, NEON_CYAN).convert("RGBA")
        canvas.paste(grad_pill, (0, 0), border_mask)
        text_x = pill_x0 + pad_x - bbox[0]
        text_y = pill_y0 + pad_y - bbox[1]
        draw.text((text_x, text_y), cta_text, font=pill_font, fill=BG_DARK, direction="rtl")

    buf = io.BytesIO()
    buf.name = "novatunnel_promo.png"
    canvas.convert("RGB").save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf
