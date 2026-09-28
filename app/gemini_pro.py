import os
import httpx

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Force Gemini requests to use IPv4-compatible HTTPX connection
transport = httpx.HTTPTransport(
    local_address="0.0.0.0"
)

http_client = httpx.Client(
    transport=transport,
    timeout=60
)

http_options = types.HttpOptions(
    httpx_client=http_client
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=http_options
)


def generate_story(outline):
    """
    Generates a full comic-style story from the 5-panel outline.
    """

    formatted_outline = "\n".join(
        [
            f"Panel {panel['number']}: {panel['title']}\n"
            f"Scene: {panel['scene']}"
            for panel in outline
        ]
    )

    prompt = f"""
You are a professional comic book writer.

Expand the following 5-panel comic outline into a complete
comic-style story.

PANEL OUTLINE:
{formatted_outline}

Requirements:

1. Create a clear and engaging story.
2. Keep the story connected from Panel 1 to Panel 5.
3. Provide narration for every panel.
4. Provide character dialogue for every panel.
5. Keep the characters and events consistent.
6. Make the story suitable for a comic book.
7. Clearly label Panel 1, Panel 2, Panel 3, Panel 4 and Panel 5.
8. For each panel include:
   - Narration
   - Dialogue

Return the complete story as formatted text.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:

        print(
            "STORY ERROR:",
            repr(e)
        )

        return (
            f"Error generating story: {str(e)}"
        )