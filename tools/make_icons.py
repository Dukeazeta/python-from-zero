"""Draw the course icon as PNG/ICO files (for browsers that don't use assets/favicon.svg).

The drawing matches assets/favicon.svg: a Graphite tile, an Eggshell ">" and a
Research Blue cursor. Run from the course folder:  python tools/make_icons.py
Writes favicon.ico (16, 32, 48 px) and assets/apple-touch-icon.png (180 px).
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
GRAPHITE, EGGSHELL, BLUE = "#2e2e2e", "#fdfcfb", "#207dff"


def draw(size, radius=8):
    s = 16  # draw large, then shrink, for smooth edges
    big = size * s
    k = big / 32  # the SVG's 32-unit grid
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=radius * k, fill=GRAPHITE)
    w = round(3.2 * k)
    points = [(9 * k, 10 * k), (15 * k, 16 * k), (9 * k, 22 * k)]
    d.line(points, fill=EGGSHELL, width=w, joint="curve")
    for x, y in (points[0], points[2]):  # round line caps
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=EGGSHELL)
    d.rounded_rectangle([17 * k, 19.4 * k, 24.5 * k, 22.6 * k], radius=1.6 * k, fill=BLUE)
    return img.resize((size, size), Image.LANCZOS)


def main():
    draw(48).save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # iOS rounds the corners itself, so the touch icon is a full square.
    draw(180, radius=0).save(ROOT / "assets" / "apple-touch-icon.png")
    print("Wrote favicon.ico and assets/apple-touch-icon.png")


if __name__ == "__main__":
    main()
