#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = PROJECT_ROOT / "public" / "thumbnail_.jpg"
DEFAULT_SOURCE = PROJECT_ROOT / "public" / "thumbnail_3.jpg"
DEFAULT_OUTPUT = PROJECT_ROOT / "public" / "thumbnail.jpg"
DEFAULT_QUALITY = 90


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def parse_crop_box(value: str) -> tuple[int, int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "--crop-box must be four comma-separated numbers: left,top,right,bottom"
        )

    try:
        left, top, right, bottom = (int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--crop-box values must be integers"
        ) from exc

    if left >= right or top >= bottom:
        raise argparse.ArgumentTypeError(
            "--crop-box must satisfy left < right and top < bottom"
        )

    return left, top, right, bottom


def get_target_size(reference_path: Path) -> tuple[int, int]:
    with Image.open(reference_path) as reference:
        return reference.size


def normalize_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def crop_by_box(
    image: Image.Image,
    crop_box: tuple[int, int, int, int],
) -> Image.Image:
    image_width, image_height = image.size
    left, top, right, bottom = crop_box

    if left < 0 or top < 0 or right > image_width or bottom > image_height:
        raise ValueError(
            "crop box is outside the source image "
            f"({image_width}x{image_height}): {crop_box}"
        )

    return image.crop(crop_box)


def crop_to_target_ratio(
    image: Image.Image,
    target_width: int,
    target_height: int,
    focus_x: float,
    focus_y: float,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    source_width, source_height = image.size
    target_ratio = target_width / target_height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_height = source_height
        crop_width = round(crop_height * target_ratio)
    else:
        crop_width = source_width
        crop_height = round(crop_width / target_ratio)

    focus_x_px = round(source_width * clamp(focus_x, 0.0, 1.0))
    focus_y_px = round(source_height * clamp(focus_y, 0.0, 1.0))

    left = round(focus_x_px - crop_width / 2)
    top = round(focus_y_px - crop_height / 2)
    left = int(clamp(left, 0, source_width - crop_width))
    top = int(clamp(top, 0, source_height - crop_height))
    right = left + crop_width
    bottom = top + crop_height

    crop_box = (left, top, right, bottom)
    return image.crop(crop_box), crop_box


def save_thumbnail(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
    focus_x: float,
    focus_y: float,
    crop_box: tuple[int, int, int, int] | None,
    quality: int,
) -> None:
    target_width, target_height = get_target_size(reference_path)
    source = normalize_image(source_path)

    if crop_box is None:
        cropped, used_crop_box = crop_to_target_ratio(
            source,
            target_width,
            target_height,
            focus_x,
            focus_y,
        )
    else:
        cropped = crop_by_box(source, crop_box)
        used_crop_box = crop_box

    resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resized.save(output_path, format="JPEG", quality=quality, optimize=True)

    print(f"Reference size: {target_width}x{target_height}")
    print(f"Source size: {source.width}x{source.height}")
    print(f"Crop box: {used_crop_box}")
    print(f"Saved: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create public/thumbnail.jpg from thumbnail_2.jpg using the same "
            "width and height as thumbnail_.jpg."
        )
    )
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--focus-x",
        type=float,
        default=0.5,
        help="Horizontal focus point from 0.0 (left) to 1.0 (right).",
    )
    parser.add_argument(
        "--focus-y",
        type=float,
        default=0.5,
        help="Vertical focus point from 0.0 (top) to 1.0 (bottom).",
    )
    parser.add_argument(
        "--crop-box",
        type=parse_crop_box,
        help=(
            "Exact source crop as left,top,right,bottom pixels. "
            "When set, focus-x and focus-y are ignored."
        ),
    )
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    save_thumbnail(
        source_path=args.source.expanduser().resolve(),
        reference_path=args.reference.expanduser().resolve(),
        output_path=args.output.expanduser().resolve(),
        focus_x=args.focus_x,
        focus_y=args.focus_y,
        crop_box=args.crop_box,
        quality=args.quality,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# python3 scripts/make_thumbnail.py --focus-y 0.35
# python3 scripts/make_thumbnail.py --crop-box 0,500,1280,1172
