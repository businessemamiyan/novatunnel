import io
import os

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from PIL import Image, ImageDraw, ImageFont

# پالت برند NovaTunnel: نئون بنفش-فیروزه‌ای روی زمینه سرمه‌ای تیره (هماهنگ با تم Mini App)
BG_DARK = (13, 12, 34)
NEON_PURPLE = (147, 51, 234)
NEON_CYAN = (34, 211, 238)

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Poppins-Bold.ttf")


def _gradient(size, c1, c2, horizontal=True) -> Image.Image:
    w, h = size
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)
    mask = Image.new("L", size)
    data = []
    for y in range(h):
        for x in range(w):
            t = x / max(w - 1, 1) if horizontal else y / max(h - 1, 1)
            data.append(int(255 * t))
    mask.putdata(data)
    return Image.composite(top, base, mask)


def _rounded_mask(size, radius) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


def _build_logo(width: int, height: int) -> Image.Image:
    """بج لوگو: نشان حلقه‌ای + وردمارک «NovaTunnel» با گرادیان نئون، روی زمینه تیره با حاشیه گرادیانی."""
    scale = 4
    w, h = width * scale, height * scale
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    radius = h // 3

    badge_mask = _rounded_mask((w, h), radius)
    bg = Image.new("RGBA", (w, h), BG_DARK + (255,))
    canvas.paste(bg, (0, 0), badge_mask)

    grad_border = _gradient((w, h), NEON_PURPLE, NEON_CYAN).convert("RGBA")
    border_mask = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(border_mask)
    border_width = max(3, h // 18)
    bd.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, outline=255, width=border_width)
    canvas.paste(grad_border, (0, 0), border_mask)

    draw = ImageDraw.Draw(canvas)

    # نشان حلقه‌ای مینیمال سمت چپ
    icon_d = int(h * 0.62)
    icon_cx = int(h * 0.62)
    icon_cy = h // 2
    draw.ellipse(
        [icon_cx - icon_d // 2, icon_cy - icon_d // 2, icon_cx + icon_d // 2, icon_cy + icon_d // 2],
        outline=NEON_CYAN + (255,), width=max(3, icon_d // 7),
    )
    inner_d = int(icon_d * 0.38)
    draw.ellipse(
        [icon_cx - inner_d // 2, icon_cy - inner_d // 2, icon_cx + inner_d // 2, icon_cy + inner_d // 2],
        fill=NEON_PURPLE + (255,),
    )

    # وردمارک متنی با گرادیان
    text = "NovaTunnel"
    text_area_x0 = int(h * 1.05)
    text_area_w = w - text_area_x0 - int(h * 0.22)

    font_size = int(h * 0.46)
    font = ImageFont.truetype(FONT_PATH, font_size)
    while font_size > 8:
        font = ImageFont.truetype(FONT_PATH, font_size)
        bbox = font.getbbox(text)
        if (bbox[2] - bbox[0]) <= text_area_w:
            break
        font_size -= 2

    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = text_area_x0 + max(0, (text_area_w - tw) // 2) - bbox[0]
    ty = (h - th) // 2 - bbox[1]

    text_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(text_mask).text((tx, ty), text, font=font, fill=255)
    text_gradient = _gradient((w, h), NEON_CYAN, NEON_PURPLE).convert("RGBA")
    canvas.paste(text_gradient, (0, 0), text_mask)

    return canvas.resize((width, height), Image.LANCZOS)


def generate_branded_qr(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=14, border=3)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask(
            back_color=(255, 255, 255),
            center_color=NEON_CYAN,
            edge_color=NEON_PURPLE,
        ),
    ).convert("RGBA")

    logo_w = int(img.size[0] * 0.46)
    logo_h = int(img.size[1] * 0.16)
    logo = _build_logo(logo_w, logo_h)

    pos = ((img.size[0] - logo_w) // 2, (img.size[1] - logo_h) // 2)
    img.alpha_composite(logo, pos)

    buf = io.BytesIO()
    buf.name = "novatunnel_qr.png"
    img.convert("RGB").save(buf, "PNG")
    buf.seek(0)
    return buf
