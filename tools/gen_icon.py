"""exe 用の ICO ファイルを生成するスクリプト。

青グラデーション背景 + 白色 app-logo.svg。

Usage:
    python tools/gen_icon.py
"""
from __future__ import annotations

import io
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "resources" / "assets" / "app-logo.svg"
OUT = ROOT / "resources" / "assets" / "app-logo.ico"

# ICO に含めるサイズ一覧
SIZES = [16, 32, 48, 64, 128, 256]


def _gradient_image(size: int, c1: tuple, c2: tuple) -> Image.Image:
    """対角グラデーション正方形画像。"""
    img = Image.new("RGB", (size, size))
    for y in range(size):
        for x in range(size):
            t = (x / size + y / size) / 2
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            img.putpixel((x, y), (r, g, b))
    return img


def _load_svg(svg_path: Path, size: int) -> Image.Image:
    png_data = cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png_data)).convert("RGBA")


def _colorize(img: Image.Image, color: tuple) -> Image.Image:
    r, g, b = color
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _, _, _, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (r, g, b, a)
    return img


def _make_icon(size: int) -> Image.Image:
    c1 = (30, 58, 95)    # #1e3a5f
    c2 = (37, 99, 235)   # #2563eb

    # 角丸背景
    bg = _gradient_image(size, c1, c2).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = max(size // 5, 2)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(bg, mask=mask)

    # ロゴ（パディング付き）
    logo_size = int(size * 0.7)
    if logo_size < 8:
        logo_size = 8
    logo = _load_svg(SVG_PATH, logo_size)
    logo = _colorize(logo, (255, 255, 255))
    offset = (size - logo_size) // 2
    result.paste(logo, (offset, offset), logo)

    return result


def main() -> None:
    images = [_make_icon(s) for s in SIZES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(str(OUT), format="ICO", sizes=[(s, s) for s in SIZES], append_images=images[1:])
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
