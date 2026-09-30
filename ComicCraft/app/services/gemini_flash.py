import time

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import OutlineResponse


class GeminiOutline(BaseModel):
    panels: list[dict] = Field(
        description="Exactly five comic panel objects."
    )


def _client() -> genai.Client:
    settings = get_settings()

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the .env file."
        )

    return genai.Client(api_key=settings.gemini_api_key)


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> list[dict]:

    settings = get_settings()

    prompt = f"""
Create a cohesive {settings.panel_count}-panel comic outline.

User story idea: {story_prompt}
Main character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}

Return exactly {settings.panel_count} panels.

Every panel must contain:
- panel_number: integer 1..{settings.panel_count}
- title: short title
- scene_description: 1-2 sentences describing the action and environment
- image_prompt: a detailed visual prompt for an image generator

Maintain the same character identity, clothing, setting,
and visual style across panels.

Do not add commentary outside the JSON.
""".strip()

    client = _client()

    max_retries = 3
    response = None

    for attempt in range(1, max_retries + 1):

        try:
            response = client.models.generate_content(
                model=settings.gemini_flash_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    response_mime_type="application/json",
                    response_schema=OutlineResponse,
                ),
            )

            print("Gemini request successful!")
            break

        except Exception as e:

            error_text = str(e)

            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt < max_retries:

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying... ({attempt}/{max_retries})"
                    )

                    time.sleep(5)

                else:

                    raise RuntimeError(
                        "Gemini service is temporarily unavailable. "
                        "Please try again later."
                    ) from e

            else:
                raise

    if response is None:
        raise RuntimeError(
            "Gemini did not return a response."
        )

    if not response.parsed:
        raise RuntimeError(
            "Gemini returned no structured outline."
        )

    panels = [
        panel.model_dump()
        for panel in response.parsed.panels
    ]

    if len(panels) != settings.panel_count:
        raise RuntimeError(
            f"Gemini returned {len(panels)} panels; "
            f"expected {settings.panel_count}."
        )

    return panels