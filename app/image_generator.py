import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

hf_client = InferenceClient(
    api_key=os.getenv("HF_TOKEN"),
    provider="auto"
)


def generate_image(prompt):
    """
    Generates a comic illustration using Hugging Face.
    """

    try:
        image = hf_client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )

        return image

    except Exception as e:
        print("IMAGE GENERATION ERROR:", repr(e))
        return None