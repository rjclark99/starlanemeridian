#!/usr/bin/env python3
"""Derive deterministic app, TV banner, and web assets from the approved brand artwork."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "branding"
EMBLEM = BRAND / "starlane-meridian-emblem-v2.png"
BACKGROUND = BRAND / "starlane-meridian-home-1920x1080.jpg"


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    clone = image.copy()
    clone.thumbnail(size, Image.Resampling.LANCZOS)
    return clone


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windows = Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(windows), size) if windows.is_file() else ImageFont.load_default()


def main() -> None:
    emblem = Image.open(EMBLEM).convert("RGBA")
    background = Image.open(BACKGROUND).convert("RGB")
    android = ROOT / "android-app" / "app" / "src" / "main" / "res" / "drawable-nodpi"
    android.mkdir(parents=True, exist_ok=True)

    icon = Image.new("RGBA", (512, 512), "#050B14")
    mark = contain(emblem, (390, 390))
    icon.alpha_composite(mark, ((512 - mark.width) // 2, (512 - mark.height) // 2))
    icon.save(android / "starlane_icon.png", optimize=True)

    banner = cover(background, (320, 180)).convert("RGBA")
    banner.alpha_composite(Image.new("RGBA", banner.size, (5, 11, 20, 112)))
    banner_mark = contain(emblem, (104, 104))
    banner.alpha_composite(banner_mark, (18, (180 - banner_mark.height) // 2))
    draw = ImageDraw.Draw(banner)
    draw.text((133, 58), "STARLANE", font=font(19, True), fill="#F4FAFF")
    draw.text((133, 82), "MERIDIAN", font=font(19, True), fill="#F4FAFF")
    draw.line((134, 112, 286, 112), fill="#67E8C4", width=2)
    draw.text((133, 121), "YOUR MEDIA. ON COURSE.", font=font(8), fill="#91A8C0")
    banner.convert("RGB").save(android / "starlane_tv_banner.jpg", quality=93, optimize=True)

    web_mark = contain(emblem, (128, 128))
    web_mark.save(ROOT / "admin-portal" / "wwwroot" / "starlane-emblem.png", optimize=True)

    print(android / "starlane_icon.png")
    print(android / "starlane_tv_banner.jpg")
    print(ROOT / "admin-portal" / "wwwroot" / "starlane-emblem.png")


if __name__ == "__main__":
    main()
