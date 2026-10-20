# -*- coding: utf-8 -*-
"""生成 PWA 图标（192 / 512）。"""
from PIL import Image, ImageDraw, ImageFont

TEAL = (13, 148, 136)   # #0D9488
WHITE = (255, 255, 255)


def make_icon(size, path):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size, size], radius=size // 5, fill=TEAL)

    text = "健"
    font = None
    for fp in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        try:
            font = ImageFont.truetype(fp, int(size * 0.55))
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), text, font=font, fill=WHITE)
    img.save(path)
    print("saved", path, f"{size}x{size}")


make_icon(192, "icon-192.png")
make_icon(512, "icon-512.png")
print("ICONS OK")
