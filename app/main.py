from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER

import os
import json
import html


# --------------------------------------------------
# LOAD ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator"
)


# --------------------------------------------------
# STATIC FILES AND TEMPLATES
# --------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

templates = Jinja2Templates(
    directory="app/templates"
)


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# --------------------------------------------------
# STEP 1: GENERATE 5-PANEL OUTLINE
# --------------------------------------------------

@app.post("/generate", response_class=HTMLResponse)
async def generate_outline_page(
    request: Request,
    theme: str = Form(...),
    character: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):

    story_prompt = f"""
Story Theme: {theme}

Main Character: {character}

Setting: {setting}

Tone: {tone}

Art Style: {art_style}
"""

    print("\nGenerating 5-panel outline...")

    outline = generate_outline(story_prompt)

    if outline.get("error"):
        print("OUTLINE ERROR:", outline["error"])

    comic = {
        "title": outline.get(
            "title",
            "ComicCraft Story"
        ),

        "theme": theme,

        "character": character,

        "setting": setting,

        "tone": tone,

        "art_style": art_style,

        "panels": outline.get(
            "panels",
            []
        )
    }

    outline_json = json.dumps(
        comic["panels"]
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "comic": comic,
            "outline_json": outline_json,
            "stage": "outline",
            "story": None,
            "pdf": None
        }
    )


# --------------------------------------------------
# STEP 2: GENERATE FULL STORY + IMAGES + PDF
# --------------------------------------------------

@app.post("/generate-story", response_class=HTMLResponse)
async def generate_story_page(
    request: Request,

    outline_json: str = Form(...),

    title: str = Form(...),
    theme: str = Form(...),
    character: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):

    try:

        # ------------------------------------------
        # Convert outline JSON back into Python
        # ------------------------------------------

        panels = json.loads(outline_json)

        print("\nGenerating complete comic story...")

        # ------------------------------------------
        # Generate full story using Gemini
        # ------------------------------------------

        story = generate_story(panels)

        # ------------------------------------------
        # Generate images for all 5 panels
        # ------------------------------------------

        for panel in panels:

            image_prompt = panel.get(
                "image_prompt",
                panel.get("scene", "")
            )

            try:

                print(
                    f"Generating image for Panel "
                    f"{panel['number']}..."
                )

                image = generate_image(
                    image_prompt
                )

                if image is not None:

                    image_path = (
                        f"app/static/"
                        f"panel_{panel['number']}.png"
                    )

                    image.save(image_path)

                    panel["image"] = (
                        f"/static/"
                        f"panel_{panel['number']}.png"
                    )

                else:

                    panel["image"] = None

            except Exception as e:

                print(
                    "IMAGE ERROR:",
                    repr(e)
                )

                panel["image"] = None

        # ------------------------------------------
        # Create final comic object
        # ------------------------------------------

        comic = {

            "title": title,

            "theme": theme,

            "character": character,

            "setting": setting,

            "tone": tone,

            "art_style": art_style,

            "panels": panels
        }

        # ------------------------------------------
        # Create PDF
        # ------------------------------------------

        pdf_path = "app/static/comic.pdf"

        create_pdf(
            comic,
            story,
            pdf_path
        )

        comic["pdf"] = "/static/comic.pdf"

        print("\nCOMIC CREATED SUCCESSFULLY!")

    except Exception as e:

        print(
            "STORY GENERATION ERROR:",
            repr(e)
        )

        story = (
            "Unable to generate the complete story. "
            "Please try again."
        )

        comic = {

            "title": title,

            "theme": theme,

            "character": character,

            "setting": setting,

            "tone": tone,

            "art_style": art_style,

            "panels": [],

            "pdf": None
        }

    # ----------------------------------------------
    # Show final result
    # ----------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "comic": comic,
            "outline_json": "",
            "stage": "final",
            "story": story,
            "pdf": comic.get("pdf")
        }
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
async def health_check():

    return {
        "status": "success",
        "message": "ComicCraft is running!"
    }


# --------------------------------------------------
# CREATE PDF
# --------------------------------------------------

def create_pdf(
    comic,
    story,
    pdf_path
):

    os.makedirs(
        "app/static",
        exist_ok=True
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ComicTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "PanelHeading",
        parent=styles["Heading2"],
        fontSize=16,
        spaceAfter=10
    )

    story_heading_style = ParagraphStyle(
        "StoryHeading",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=15
    )

    normal_style = ParagraphStyle(
        "ComicText",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=10
    )

    document = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    pdf_story = []

    # ----------------------------------------------
    # TITLE
    # ----------------------------------------------

    pdf_story.append(
        Paragraph(
            html.escape(
                comic["title"]
            ),
            title_style
        )
    )

    # ----------------------------------------------
    # COMIC INFORMATION
    # ----------------------------------------------

    pdf_story.append(
        Paragraph(
            f"<b>Theme:</b> "
            f"{html.escape(comic['theme'])}",
            normal_style
        )
    )

    pdf_story.append(
        Paragraph(
            f"<b>Main Character:</b> "
            f"{html.escape(comic['character'])}",
            normal_style
        )
    )

    pdf_story.append(
        Paragraph(
            f"<b>Setting:</b> "
            f"{html.escape(comic['setting'])}",
            normal_style
        )
    )

    pdf_story.append(
        Paragraph(
            f"<b>Tone:</b> "
            f"{html.escape(comic['tone'])}",
            normal_style
        )
    )

    pdf_story.append(
        Paragraph(
            f"<b>Art Style:</b> "
            f"{html.escape(comic['art_style'])}",
            normal_style
        )
    )

    pdf_story.append(
        Spacer(1, 20)
    )

    # ----------------------------------------------
    # FULL STORY
    # ----------------------------------------------

    pdf_story.append(
        Paragraph(
            "Full Story",
            story_heading_style
        )
    )

    safe_story = html.escape(
        story
    )

    # Convert line breaks into paragraphs
    for paragraph in safe_story.split("\n"):

        paragraph = paragraph.strip()

        if paragraph:

            pdf_story.append(
                Paragraph(
                    paragraph,
                    normal_style
                )
            )

    pdf_story.append(
        PageBreak()
    )

    # ----------------------------------------------
    # PANELS
    # ----------------------------------------------

    for panel in comic["panels"]:

        pdf_story.append(
            Paragraph(
                f"Panel {panel['number']}: "
                f"{html.escape(panel.get('title', ''))}",
                heading_style
            )
        )

        # ------------------------------------------
        # IMAGE
        # ------------------------------------------

        image_url = panel.get("image")

        if image_url:

            image_path = image_url.replace(
                "/static/",
                "app/static/"
            )

            if os.path.exists(image_path):

                try:

                    img_reader = ImageReader(
                        image_path
                    )

                    img_width, img_height = (
                        img_reader.getSize()
                    )

                    max_width = 500
                    max_height = 330

                    scale = min(
                        max_width / img_width,
                        max_height / img_height
                    )

                    display_width = (
                        img_width * scale
                    )

                    display_height = (
                        img_height * scale
                    )

                    comic_image = Image(
                        image_path,
                        width=display_width,
                        height=display_height
                    )

                    pdf_story.append(
                        comic_image
                    )

                    pdf_story.append(
                        Spacer(1, 12)
                    )

                except Exception as e:

                    print(
                        "PDF IMAGE ERROR:",
                        repr(e)
                    )

        # ------------------------------------------
        # SCENE
        # ------------------------------------------

        pdf_story.append(
            Paragraph(
                f"<b>Scene:</b> "
                f"{html.escape(panel.get('scene', ''))}",
                normal_style
            )
        )

        # ------------------------------------------
        # IMAGE PROMPT
        # ------------------------------------------

        pdf_story.append(
            Paragraph(
                f"<b>Image Prompt:</b> "
                f"{html.escape(panel.get('image_prompt', ''))}",
                normal_style
            )
        )

        pdf_story.append(
            PageBreak()
        )

    # ----------------------------------------------
    # BUILD PDF
    # ----------------------------------------------

    document.build(
        pdf_story
    )

    print(
        "PDF CREATED:",
        pdf_path
    )