from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/SFNSDisplay-Bold.otf" if bold else "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGB", size)
    pixels = image.load()
    for y_position in range(height):
        ratio = y_position / max(1, height - 1)
        color = tuple(round(top[index] * (1 - ratio) + bottom[index] * ratio) for index in range(3))
        for x_position in range(width):
            pixels[x_position, y_position] = color
    return image


def add_machine_path(draw: ImageDraw.ImageDraw, origin: tuple[int, int], scale: float) -> None:
    x_origin, y_origin = origin
    path = [
        (0, 70),
        (0, 0),
        (92, 0),
        (92, 68),
        (22, 68),
        (22, 20),
        (70, 20),
        (70, 48),
        (43, 48),
        (43, 38),
    ]
    points = [(x_origin + round(x * scale), y_origin + round(y * scale)) for x, y in path]
    draw.line(points, fill="#ff7a3d", width=max(3, round(8 * scale)), joint="curve")
    end_x, end_y = points[-1]
    radius = max(4, round(7 * scale))
    draw.ellipse((end_x - radius, end_y - radius, end_x + radius, end_y + radius), fill="#ffe3d6")


def generate_icon() -> None:
    size = 1_024
    image = vertical_gradient((size, size), (29, 38, 50), (10, 14, 20)).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((20, 20, size - 20, size - 20), radius=230, fill=255)
    image.putalpha(mask)

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((190, 145, 880, 835), fill=(229, 107, 47, 78))
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    image = Image.alpha_composite(image, glow)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((155, 175, 869, 849), radius=80, outline="#46576b", width=18)
    draw.line((245, 720, 245, 300, 755, 300), fill="#718399", width=18, joint="curve")
    add_machine_path(draw, (292, 388), 4.35)
    draw.ellipse((214, 690, 278, 754), fill="#6ce5a5", outline="#d8ffeb", width=8)
    image.save(ASSETS / "app-icon-1024.png", optimize=True)


def generate_social_preview() -> None:
    width, height = 1_280, 640
    image = vertical_gradient((width, height), (22, 29, 39), (8, 12, 18)).convert("RGBA")

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((740, -170, 1_420, 510), fill=(229, 107, 47, 76))
    glow_draw.ellipse((-200, 350, 520, 950), fill=(62, 128, 167, 42))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    image = Image.alpha_composite(image, glow)

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((62, 54, 170, 162), radius=26, fill="#1c2632", outline="#46576b", width=3)
    add_machine_path(draw, (82, 82), 0.74)
    draw.text((62, 210), "LaserGRBL", font=font(72, bold=True), fill="#ffffff")
    draw.text((62, 292), "for macOS", font=font(56, bold=True), fill="#ff7a3d")
    draw.text((65, 375), "Control. Preview. Engrave.", font=font(27), fill="#b9c5d3")

    pills = ["GRBL 1.1", "Safe streaming", "Image → G-code", "Open source"]
    x_position = 64
    for label in pills:
        label_font = font(17, bold=True)
        bounds = draw.textbbox((0, 0), label, font=label_font)
        pill_width = bounds[2] - bounds[0] + 34
        draw.rounded_rectangle(
            (x_position, 458, x_position + pill_width, 501), radius=21, fill="#202b38", outline="#3f4f62", width=2
        )
        draw.text((x_position + 17, 468), label, font=label_font, fill="#dce5ef")
        x_position += pill_width + 12

    card = (750, 96, 1_214, 550)
    draw.rounded_rectangle(card, radius=26, fill="#151c25", outline="#344356", width=3)
    draw.rounded_rectangle((785, 133, 1_179, 190), radius=12, fill="#202a36")
    draw.ellipse((808, 153, 824, 169), fill="#6ce5a5")
    draw.text((842, 147), "GRBL controller connected", font=font(18, bold=True), fill="#dfe9f3")
    draw.line((814, 467, 814, 243, 1_117, 243), fill="#566a80", width=5, joint="curve")
    add_machine_path(draw, (842, 286), 2.45)
    draw.rounded_rectangle((792, 485, 1_172, 519), radius=16, fill="#251d19")
    draw.rounded_rectangle((792, 485, 1_079, 519), radius=16, fill="#e56b2f")
    draw.text((65, 564), "github.com/alexkypraiou/LaserGRBL-MacOS-Controller", font=font(18), fill="#7f8d9d")
    image.convert("RGB").save(ASSETS / "social-preview.png", optimize=True, quality=95)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    generate_icon()
    generate_social_preview()


if __name__ == "__main__":
    main()
