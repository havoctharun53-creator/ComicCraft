from pathlib import Path
from fpdf import FPDF


BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXPORTS_DIR = BASE_DIR / "static" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(value) -> str:
    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\n": " ",
        "\r": " ",
        "\t": " ",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Break extremely long words/strings
    words = text.split(" ")

    fixed_words = []

    for word in words:
        if len(word) > 40:
            chunks = [
                word[i:i + 35]
                for i in range(0, len(word), 35)
            ]
            fixed_words.extend(chunks)
        else:
            fixed_words.append(word)

    return " ".join(fixed_words)


def save_pdf(layout: list[dict]) -> str:

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_margins(
        15,
        15,
        15,
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15,
    )

    pdf.add_page()

    # -------------------------
    # TITLE
    # -------------------------

    pdf.set_font(
        "Helvetica",
        "B",
        20,
    )

    pdf.cell(
        180,
        12,
        "ComicCraft",
        align="C",
    )

    pdf.ln(15)

    # -------------------------
    # PANELS
    # -------------------------

    for index, panel in enumerate(layout):

        panel_number = panel.get(
            "panel_number",
            index + 1,
        )

        title = clean_text(
            panel.get(
                "title",
                f"Panel {panel_number}",
            )
        )

        description = clean_text(
            panel.get(
                "scene_description",
                "",
            )
        )

        narration = clean_text(
            panel.get(
                "narration",
                "",
            )
        )

        dialogue = clean_text(
            panel.get(
                "dialogue",
                "",
            )
        )

        # If description is empty, use narration
        if not description:
            description = narration

        # -------------------------
        # PANEL TITLE
        # -------------------------

        pdf.set_font(
            "Helvetica",
            "B",
            13,
        )

        pdf.multi_cell(
            180,
            8,
            f"Panel {panel_number}: {title}",
            border=1,
        )

        # -------------------------
        # DESCRIPTION
        # -------------------------

        if description:

            pdf.set_font(
                "Helvetica",
                "",
                10,
            )

            pdf.multi_cell(
                180,
                6,
                description,
                border=1,
            )

        # -------------------------
        # DIALOGUE
        # -------------------------

        if dialogue:

            pdf.set_font(
                "Helvetica",
                "I",
                10,
            )

            pdf.multi_cell(
                180,
                6,
                "Dialogue: " + dialogue,
                border=1,
            )

        pdf.ln(6)

    # -------------------------
    # SAVE
    # -------------------------

    output_file = (
        EXPORTS_DIR / "comiccraft_comic.pdf"
    )

    pdf.output(
        str(output_file)
    )

    return str(output_file)