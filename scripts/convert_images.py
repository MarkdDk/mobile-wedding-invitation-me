#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_INPUT_DIR = Path("/Users/ddk/Downloads/convert")
DEFAULT_OUTPUT_DIR = Path(
    "/Users/ddk/Desktop/WS/wedding_invitation/"
    "mobile-wedding-invitation-me/src/assets/images_all"
)

IMAGE_EXTENSIONS = {
    ".bmp",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

TARGET_WIDTH = 1280
TARGET_HEIGHT = 1920
TARGET_BYTES = 460_000


@dataclass(frozen=True)
class ConvertResult:
    src: str
    dst: str
    size: int
    quality: int


def iter_images(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def fit_on_white_canvas(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    image.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), "white")
    x = (TARGET_WIDTH - image.width) // 2
    y = (TARGET_HEIGHT - image.height) // 2

    if image.mode == "RGBA":
        canvas.paste(image, (x, y), image)
    else:
        canvas.paste(image.convert("RGB"), (x, y))

    return canvas


def encode_jpeg(image: Image.Image, quality: int) -> bytes:
    output = BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=quality,
        subsampling=2,
        optimize=False,
        progressive=False,
    )
    return output.getvalue()


def encode_near_target(image: Image.Image, target_bytes: int) -> tuple[bytes, int]:
    low = 1
    high = 100
    best_bytes = b""
    best_quality = low
    best_delta = float("inf")

    for _ in range(7):
        quality = (low + high) // 2
        data = encode_jpeg(image, quality)
        delta = abs(len(data) - target_bytes)

        if delta < best_delta:
            best_bytes = data
            best_quality = quality
            best_delta = delta

        if len(data) < target_bytes:
            low = quality + 1
        else:
            high = quality - 1

    return best_bytes, best_quality


def output_path_for(src: Path, input_dir: Path, output_dir: Path) -> Path:
    relative = src.relative_to(input_dir).with_suffix(".jpg")
    return output_dir / relative


def convert_one(args: tuple[str, str, str, int]) -> ConvertResult:
    src_raw, input_dir_raw, output_dir_raw, target_bytes = args
    src = Path(src_raw)
    input_dir = Path(input_dir_raw)
    output_dir = Path(output_dir_raw)
    dst = output_path_for(src, input_dir, output_dir)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(src) as image:
        converted = fit_on_white_canvas(image)
        data, quality = encode_near_target(converted, target_bytes)

    dst.write_bytes(data)

    return ConvertResult(
        src=str(src),
        dst=str(dst),
        size=len(data),
        quality=quality,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resize images to 1280x1920 with white padding and save JPGs "
            "near a target byte size."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-bytes", type=int, default=TARGET_BYTES)
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, (os.cpu_count() or 2) - 1),
        help="Parallel worker count. Default: CPU count minus one.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()
    images = iter_images(input_dir)

    if not images:
        print(f"No images found in {input_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"Converting {len(images)} images -> {output_dir} "
        f"({TARGET_WIDTH}x{TARGET_HEIGHT}, target {args.target_bytes:,} bytes)"
    )

    jobs = [
        (str(path), str(input_dir), str(output_dir), args.target_bytes)
        for path in images
    ]

    done = 0
    failures: list[tuple[str, str]] = []
    sizes: list[int] = []

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(convert_one, job): job[0] for job in jobs}
        for future in as_completed(futures):
            src = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001 - report and keep batch running.
                failures.append((src, str(exc)))
                continue

            done += 1
            sizes.append(result.size)
            if done % 25 == 0 or done == len(images):
                print(f"{done}/{len(images)} converted")

    if sizes:
        print(
            "Done: "
            f"{done} converted, "
            f"min {min(sizes):,} bytes, "
            f"max {max(sizes):,} bytes, "
            f"avg {sum(sizes) // len(sizes):,} bytes"
        )

    if failures:
        print(f"Failed: {len(failures)}")
        for src, message in failures[:20]:
            print(f"- {src}: {message}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
