#!/usr/bin/env python3
"""
TrailFeathers - Split weather_ducks.png into 7 individual icon files (static/images_for_site/weather_icons/).
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from pathlib import Path

from PIL import Image

SRC = Path(__file__).resolve().parent.parent / "static/images_for_site/weather_ducks.png"
OUT_DIR = Path(__file__).resolve().parent.parent / "static/images_for_site/weather_icons"
# Order: top row left→right, middle row left→right, bottom center
NAMES = [
    "sunny",
    "rain",
    "snow",
    "windy",
    "fog",
    "partly_cloudy",
    "error",
]


def main():
    im = Image.open(SRC)
    w, h = im.size
    if w != 1024 or h != 1024:
        raise SystemExit(f"Expected 1024x1024, got {w}x{h}")

    cw = w // 3  # column width
    ch = h // 3  # row height
    # Middle row ends above the error duck; error duck starts in the overlap so it's not cut off
    middle_bottom = 2 * ch - 50  # 632 for ch=341
    # (left, upper, right, lower) for each of 7 cells
    boxes = [
        (0, 0, cw, ch),                    # 0: top-left
        (cw, 0, 2 * cw, ch),               # 1: top-center
        (2 * cw, 0, w, ch),                # 2: top-right
        (0, ch, cw, middle_bottom),        # 3: mid-left
        (cw, ch, 2 * cw, middle_bottom),   # 4: mid-center (fog)
        (2 * cw, ch, w, middle_bottom),    # 5: mid-right
        (cw, middle_bottom, 2 * cw, h),    # 6: bottom-center (error)
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, box in zip(NAMES, boxes):
        cropped = im.crop(box)
        out_path = OUT_DIR / f"{name}.png"
        cropped.save(out_path, "PNG")
        print(out_path)

    print("Done. 7 icons saved to", OUT_DIR)


if __name__ == "__main__":
    main()
