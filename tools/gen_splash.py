"""PyInstaller Splash 用の PNG 画像を生成するスクリプト。

Usage:
    python tools/gen_splash.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 380, 260
OUT = Path(__file__).resolve().parent.parent / "resources" / "assets" / "splash.png"


def _rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _gradient_image(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        for x in range(w):
            # 対角グラデーション
            t = (x / w + y / h) / 2
            rr = int(c1[0] + (c2[0] - c1[0]) * t)
            gg = int(c1[1] + (c2[1] - c1[1]) * t)
            bb = int(c1[2] + (c2[2] - c1[2]) * t)
            img.putpixel((x, y), (rr, gg, bb))
    return img


def main() -> None:
    # グラデーション背景
    c1 = (30, 58, 95)    # #1e3a5f
    c2 = (37, 99, 235)   # #2563eb
    img = _gradient_image(WIDTH, HEIGHT, c1, c2)

    # 角丸マスク
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, WIDTH - 1, HEIGHT - 1), radius=16, fill=255)
    bg = Image.new("RGB", (WIDTH, HEIGHT), (245, 247, 250))
    bg.paste(img, mask=mask)
    img = bg

    draw = ImageDraw.Draw(img)

    # フォント (システムフォント、なければデフォルト)
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_ver = ImageFont.truetype("arial.ttf", 13)
        font_msg = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_ver = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
            font_msg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        except OSError:
            font_title = ImageFont.load_default()
            font_ver = ImageFont.load_default()
            font_msg = ImageFont.load_default()

    # ロゴ代わりの丸いアイコン
    cx = WIDTH // 2
    draw.ellipse((cx - 28, 40, cx + 28, 96), fill=(96, 165, 250))  # #60a5fa
    # B の文字
    try:
        font_logo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except OSError:
        font_logo = font_title
    bb = draw.textbbox((0, 0), "B", font=font_logo)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((cx - tw // 2, 68 - th // 2 - bb[1]), "B", fill="white", font=font_logo)

    # タイトル
    bb = draw.textbbox((0, 0), "Bunseki", font=font_title)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, 110), "Bunseki", fill="white", font=font_title)

    # バージョン
    ver = "v1.0"
    bb = draw.textbbox((0, 0), ver, font=font_ver)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, 148), ver, fill=(255, 255, 255, 150), font=font_ver)

    # プログレスバー風のライン
    bar_y = 190
    draw.rounded_rectangle(
        (60, bar_y, WIDTH - 60, bar_y + 4),
        radius=2,
        fill=(255, 255, 255, 40),
    )
    draw.rounded_rectangle(
        (60, bar_y, 60 + (WIDTH - 120) // 3, bar_y + 4),
        radius=2,
        fill=(96, 165, 250),
    )

    # メッセージ
    msg = "Loading..."
    bb = draw.textbbox((0, 0), msg, font=font_msg)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, 206), msg, fill=(255, 255, 255, 180), font=font_msg)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT), "PNG")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
