from pathlib import Path

from app.schemas import PromptRequest
from app.services.exporters import save_pdf
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image, _demo_image
from app.services.layout_builder import build_comic_layout


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


def create_fallback_outline(request: PromptRequest) -> list[dict]:
    return [
        {
            "panel_number": 1,
            "title": "The Discovery",
            "scene_description": f"{request.character_name} discovers a mysterious glowing key in {request.setting}.",
            "image_prompt": f"{request.character_name} discovering a glowing mysterious key in {request.setting}, {request.art_style} comic style",
        },
        {
            "panel_number": 2,
            "title": "The Secret Door",
            "scene_description": f"{request.character_name} uses the key and discovers a secret magical door.",
            "image_prompt": f"{request.character_name} opening a secret magical door with a glowing key, {request.setting}, {request.art_style} comic style",
        },
        {
            "panel_number": 3,
            "title": "The Magical City",
            "scene_description": f"{request.character_name} enters a magical city filled with friendly robots.",
            "image_prompt": f"{request.character_name} entering a magical city with friendly robots, colorful fantasy world, {request.art_style} comic style",
        },
        {
            "panel_number": 4,
            "title": "The Challenge",
            "scene_description": f"{request.character_name} works with a friendly robot to solve a difficult puzzle.",
            "image_prompt": f"{request.character_name} and a friendly robot solving a mysterious puzzle, magical city, {request.art_style} comic style",
        },
        {
            "panel_number": 5,
            "title": "The Happy Ending",
            "scene_description": f"{request.character_name} saves the magical city and safely returns home.",
            "image_prompt": f"{request.character_name} celebrating after saving the magical city and returning home, happy ending, {request.art_style} comic style",
        },
    ]


def create_fallback_story(outline: list[dict]) -> list[dict]:
    return [
        {
            "panel_number": panel["panel_number"],
            "narration": panel["scene_description"],
            "dialogue": "",
        }
        for panel in outline
    ]


def generate_comic(request: PromptRequest) -> tuple[list[dict], str]:

    # 1. OUTLINE
    try:
        outline = generate_outline(
            request.story_prompt,
            request.character_name,
            request.setting,
            request.tone,
            request.art_style,
        )
        print("Gemini outline generated successfully.")

    except Exception as exc:
        print(f"Gemini outline unavailable: {exc}")
        print("Using fallback 5-panel outline...")
        outline = create_fallback_outline(request)

    if len(outline) != 5:
        outline = create_fallback_outline(request)

    # 2. STORY
    try:
        story = generate_story(
            outline,
            request.story_prompt,
            request.character_name,
            request.setting,
            request.tone,
        )
        print("Gemini story generated successfully.")

    except Exception as exc:
        print(f"Gemini story unavailable: {exc}")
        print("Using fallback story...")
        story = create_fallback_story(outline)

    # 3. IMAGES
    image_paths = []

    for panel in outline:

        panel_number = panel["panel_number"]

        try:
            print(f"Generating image for panel {panel_number}...")

            image_path = generate_image(
                panel["image_prompt"],
                panel_number,
            )

            print(f"Image generated: {image_path}")

            image_paths.append(image_path)

        except Exception as exc:

            print(
                f"AI image failed for panel {panel_number}: {exc}"
            )

            # Create demo fallback image
            filename = f"fallback_panel_{panel_number}.png"
            file_path = PANELS_DIR / filename

            _demo_image(
                panel["image_prompt"],
                panel_number,
                file_path,
            )

            image_url = f"/static/panels/{filename}"

            print(f"Fallback image created: {file_path}")

            image_paths.append(image_url)

    # 4. LAYOUT
    print("Building comic layout...")

    layout = build_comic_layout(
        outline,
        story,
        image_paths,
    )

    # 5. PDF
    print("Creating PDF...")

    pdf_path = save_pdf(layout)

    print("Comic generated successfully!")

    return layout, pdf_path