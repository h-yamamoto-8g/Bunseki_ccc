"""PyInstaller Splash 用の PNG 画像を生成するスクリプト。

Usage:
    python tools/gen_splash.py
"""
from __future__ import annotations

import io
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 380, 260
ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "resources" / "assets" / "app-logo.svg"
OUT = ROOT / "resources" / "assets" / "splash.png"


def _gradient_image(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    """対角グラデーション画像を生成する。"""
    img = Image.new("RGB", (w, h))
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            img.putpixel((x, y), (r, g, b))
    return img


def _load_svg_as_image(svg_path: Path, size: int) -> Image.Image:
    """SVG を指定サイズの RGBA Image として読み込む。"""
    png_data = cairosvg.svg2png(
        url=str(svg_path),
        output_width=size,
        output_height=size,
    )
    return Image.open(io.BytesIO(png_data)).convert("RGBA")


def _colorize_logo(logo: Image.Image, color: tuple) -> Image.Image:
    """ロゴの不透明部分を指定色で塗り替える。"""
    r, g, b = color
    pixels = logo.load()
    w, h = logo.size
    for y in range(h):
        for x in range(w):
            _, _, _, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (r, g, b, a)
    return logo


def main() -> None:
    # グラデーション背景（角丸なし・全面塗り）
    c1 = (30, 58, 95)    # #1e3a5f
    c2 = (37, 99, 235)   # #2563eb
    img = _gradient_image(WIDTH, HEIGHT, c1, c2).convert("RGBA")

    # app-logo.svg を白色で描画
    logo_size = 64
    logo = _load_svg_as_image(SVG_PATH, logo_size)
    logo = _colorize_logo(logo, (255, 255, 255))
    lx = (WIDTH - logo_size) // 2
    ly = 50
    img.paste(logo, (lx, ly), logo)

    draw = ImageDraw.Draw(img)
    cx = WIDTH // 2

    # フォント
    try:
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_sub = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        except OSError:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

    # タイトル
    bb = draw.textbbox((0, 0), "Bunseki", font=font_title)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, 128), "Bunseki", fill="white", font=font_title)

    # メッセージ
    msg = "Loading..."
    bb = draw.textbbox((0, 0), msg, font=font_sub)
    tw = bb[2] - bb[0]
    draw.text((cx - tw // 2, 200), msg, fill=(255, 255, 255, 180), font=font_sub)

    # RGB に変換して保存
    out = img.convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(OUT), "PNG")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
