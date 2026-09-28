import os
import json
import time
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


def generate_outline(story_prompt):
    """
    Generates a structured 5-panel comic outline using Gemini Flash.
    """

    prompt = f"""
You are a professional comic storyboard writer.

Create a structured 5-panel comic outline based on this user's story prompt:

{story_prompt}

The comic must contain exactly 5 panels.

For each panel provide:
1. Panel number
2. Panel title
3. Scene description
4. Image-generation prompt

Return ONLY valid JSON in this format:

{{
    "title": "Comic title",
    "panels": [
        {{
            "number": 1,
            "title": "Panel title",
            "scene": "Detailed scene description",
            "image_prompt": "Detailed prompt for generating the comic image"
        }},
        {{
            "number": 2,
            "title": "Panel title",
            "scene": "Detailed scene description",
            "image_prompt": "Detailed prompt for generating the comic image"
        }},
        {{
            "number": 3,
            "title": "Panel title",
            "scene": "Detailed scene description",
            "image_prompt": "Detailed prompt for generating the comic image"
        }},
        {{
            "number": 4,
            "title": "Panel title",
            "scene": "Detailed scene description",
            "image_prompt": "Detailed prompt for generating the comic image"
        }},
        {{
            "number": 5,
            "title": "Panel title",
            "scene": "Detailed scene description",
            "image_prompt": "Detailed prompt for generating the comic image"
        }}
    ]
}}

Make sure there are exactly 5 panels.
Do not add markdown or  around the JSON.
"""

    for attempt in range(3):

        try:
            print(
                f"Generating outline - Attempt {attempt + 1}..."
            )

            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith(""):
                text = text.replace(
                    "json",
                    ""
                )

                text = text.replace(
                    "",
                    ""
                )

                text = text.strip()

            outline = json.loads(text)

            print(
                "GENERATED OUTLINE:",
                outline
            )

            return outline

        except Exception as e:

            print(
                f"OUTLINE ATTEMPT "
                f"{attempt + 1} FAILED:",
                repr(e)
            )

            if attempt < 2:

                print(
                    "Retrying in 3 seconds..."
                )

                time.sleep(3)

    return {
        "title": "ComicCraft Story",
        "panels": [],
        "error": str(e)
    }