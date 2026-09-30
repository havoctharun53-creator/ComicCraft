from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"

PANELS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def _safe_name(value: str) -> str:
    value = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        value,
    ).strip("_")

    return value[:50] or "panel"


def _font(size: int):
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def _demo_image(
    prompt: str,
    panel_number: int,
    output: Path,
) -> None:

    # Create a real PNG image
    image = Image.new(
        "RGB",
        (900, 650),
        "white",
    )

    draw = ImageDraw.Draw(image)

    # Border
    draw.rectangle(
        (10, 10, 890, 640),
        outline="black",
        width=6,
    )

    # Header
    title_font = _font(36)
    body_font = _font(23)
    small_font = _font(18)

    draw.rectangle(
        (10, 10, 890, 90),
        fill="#eeeeee",
    )

    draw.text(
        (35, 30),
        f"COMICCRAFT - PANEL {panel_number}",
        fill="black",
        font=title_font,
    )

    # Character placeholder
    center_x = 450
    center_y = 320

    # Head
    draw.ellipse(
        (
            center_x - 70,
            center_y - 130,
            center_x + 70,
            center_y + 10,
        ),
        outline="black",
        width=5,
    )

    # Body
    draw.rectangle(
        (
            center_x - 80,
            center_y + 10,
            center_x + 80,
            center_y + 180,
        ),
        outline="black",
        width=5,
    )

    # Eyes
    draw.ellipse(
        (
            center_x - 40,
            center_y - 80,
            center_x - 20,
            center_y - 60,
        ),
        fill="black",
    )

    draw.ellipse(
        (
            center_x + 20,
            center_y - 80,
            center_x + 40,
            center_y - 60,
        ),
        fill="black",
    )

    # Speech bubble
    bubble_x1 = 570
    bubble_y1 = 150
    bubble_x2 = 850
    bubble_y2 = 260

    draw.rounded_rectangle(
        (
            bubble_x1,
            bubble_y1,
            bubble_x2,
            bubble_y2,
        ),
        radius=20,
        outline="black",
        width=4,
        fill="white",
    )

    draw.text(
        (595, 180),
        f"Panel {panel_number}",
        fill="black",
        font=body_font,
    )

    # Prompt text
    clean_prompt = str(prompt).replace(
        "\n",
        " ",
    )

    if len(clean_prompt) > 250:
        clean_prompt = clean_prompt[:250] + "..."

    words = clean_prompt.split()
    lines = []
    current = ""

    for word in words:

        test = (
            current + " " + word
        ).strip()

        if len(test) > 55:
            lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)

    y = 500

    for line in lines[:4]:

        draw.text(
            (40, y),
            line,
            fill="black",
            font=small_font,
        )

        y += 25

    draw.text(
        (40, 600),
        "ComicCraft Demo Panel",
        fill="black",
        font=small_font,
    )

    image.save(
        output,
        format="PNG",
    )


def _huggingface_image(
    prompt: str,
    output: Path,
) -> None:

    settings = get_settings()

    if not settings.hf_api_key:
        raise RuntimeError(
            "HF_API_KEY is missing."
        )

    from huggingface_hub import InferenceClient

    client = InferenceClient(
        provider=settings.hf_provider,
        api_key=settings.hf_api_key,
    )

    image = client.text_to_image(
        prompt=prompt,
        model=settings.image_model,
    )

    image.save(output)


def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    settings = get_settings()

    filename = (
        f"panel_{panel_number}_"
        f"{_safe_name(prompt)}.png"
    )

    output = PANELS_DIR / filename

    enhanced_prompt = (
        f"{prompt}. "
        f"Cohesive comic panel, expressive characters, "
        f"clear composition, strong visual storytelling, "
        f"clean line art, no readable text."
    )

    provider = (
        settings.image_provider
        .lower()
        .strip()
    )

    # ------------------------------------------------
    # DEMO MODE
    # ------------------------------------------------

    if provider == "demo":

        print(
            f"Creating demo image for panel "
            f"{panel_number}..."
        )

        _demo_image(
            prompt,
            panel_number,
            output,
        )

    # ------------------------------------------------
    # HUGGINGFACE MODE
    # ------------------------------------------------

    elif provider == "huggingface":

        try:

            print(
                f"Generating AI image for panel "
                f"{panel_number}..."
            )

            _huggingface_image(
                enhanced_prompt,
                output,
            )

        except Exception as exc:

            print(
                f"HuggingFace image failed: {exc}"
            )

            print(
                f"Creating demo image for panel "
                f"{panel_number} instead..."
            )

            _demo_image(
                prompt,
                panel_number,
                output,
            )

    # ------------------------------------------------
    # LOCAL MODE
    # ------------------------------------------------

    elif provider == "local":

        from app.config import get_settings

        local_settings = get_settings()

        import torch
        from diffusers import StableDiffusionPipeline

        device = local_settings.local_device

        if device == "auto":
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        dtype = (
            torch.float16
            if device == "cuda"
            else torch.float32
        )

        pipe = StableDiffusionPipeline.from_pretrained(
            local_settings.local_image_model,
            torch_dtype=dtype,
        )

        pipe = pipe.to(device)

        image = pipe(
            enhanced_prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
        ).images[0]

        image.save(output)

    else:

        raise RuntimeError(
            "IMAGE_PROVIDER must be "
            "huggingface, local, or demo."
        )

    print(
        f"Panel {panel_number} image saved: "
        f"{output}"
    )

    return (
        f"/static/panels/{filename}"
    )