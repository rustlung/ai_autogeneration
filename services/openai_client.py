"""
OpenAI image generation utilities.
"""
import base64
import hashlib
import logging
from pathlib import Path

from openai import OpenAI, OpenAIError, APIError, APIConnectionError, RateLimitError, APITimeoutError

import config

logger = logging.getLogger(__name__)


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def generate_image(prompt: str) -> Path:
    """
    Generate an image using OpenAI and return file path.
    
    Args:
        prompt: Image generation prompt
        
    Returns:
        Path to saved PNG file
    """
    if not config.OPENAI_IMAGE_MODEL:
        raise Exception("OPENAI_IMAGE_MODEL is not configured")

    if not config.OPENAI_IMAGE_SIZE:
        raise Exception("OPENAI_IMAGE_SIZE is not configured")

    image_hash = _prompt_hash(prompt)
    image_path = config.ASSETS_DIR / f"design_{image_hash}.png"

    if image_path.exists():
        logger.info(f"Image cache hit: {image_path}")
        return image_path

    logger.info("Image cache miss - generating image")
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    try:
        response = client.images.generate(
            model=config.OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size=config.OPENAI_IMAGE_SIZE,
            response_format="b64_json"
        )

        image_b64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)
        image_path.write_bytes(image_bytes)

        logger.info(f"Image saved: {image_path}")
        return image_path

    except APIConnectionError as e:
        logger.error(f"Network error connecting to OpenAI: {e}", exc_info=True)
        raise Exception("Network error: Unable to connect to OpenAI API. Check your internet connection.")

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}", exc_info=True)
        raise Exception("Rate limit exceeded. Please try again later or check your OpenAI plan.")

    except APITimeoutError as e:
        logger.error(f"API timeout: {e}", exc_info=True)
        raise Exception("Request timed out. Please try again.")

    except APIError as e:
        logger.error(f"OpenAI API error: {e}", exc_info=True)
        raise Exception(f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}")

    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}", exc_info=True)
        raise Exception(f"OpenAI error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in image generation: {e}", exc_info=True)
        raise
