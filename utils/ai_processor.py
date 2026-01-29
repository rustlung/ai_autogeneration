"""
AI processing module.
Handles OpenAI API calls, caching, and retry logic.
"""
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI, OpenAIError, APIError, APIConnectionError, RateLimitError, APITimeoutError
from pydantic import ValidationError

from utils.schema import (
    ReportData,
    REPORT_SCHEMA_DESCRIPTION,
    DesignBrief,
    DESIGN_BRIEF_SCHEMA_DESCRIPTION
)
from utils.io import read_json_file, write_json_file_atomic, get_cache_path, read_text_file

logger = logging.getLogger(__name__)


def compute_text_hash(text: str) -> str:
    """
    Compute SHA256 hash of text for caching.
    
    Args:
        text: Input text to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_from_cache(text: str, cache_dir: Path) -> Optional[ReportData]:
    """
    Try to load cached AI response.
    
    Args:
        text: Input text (used for hash computation)
        cache_dir: Directory containing cache files
        
    Returns:
        ReportData if cache hit and valid, None otherwise
    """
    text_hash = compute_text_hash(text)
    cache_path = get_cache_path(text_hash, cache_dir)
    
    if not cache_path.exists():
        logger.info(f"Cache miss for hash {text_hash[:8]}...")
        return None
    
    try:
        logger.info(f"Cache hit for hash {text_hash[:8]}...")
        cached_data = read_json_file(cache_path)
        report_data = ReportData(**cached_data)
        logger.info("Cache data is valid")
        return report_data
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Cached data is invalid: {e}. Will regenerate.")
        return None
    except Exception as e:
        logger.error(f"Error loading cache: {e}", exc_info=True)
        return None


def save_to_cache(text: str, report_data: ReportData, cache_dir: Path):
    """
    Save AI response to cache.
    
    Args:
        text: Input text (used for hash computation)
        report_data: Report data to cache
        cache_dir: Directory for cache files
    """
    text_hash = compute_text_hash(text)
    cache_path = get_cache_path(text_hash, cache_dir)
    
    try:
        data_dict = report_data.model_dump()
        write_json_file_atomic(cache_path, data_dict)
        logger.info(f"Saved to cache: {cache_path}")
    except Exception as e:
        logger.error(f"Failed to save cache: {e}", exc_info=True)


def get_design_brief_cache_path(text: str, cache_dir: Path) -> Path:
    """
    Generate cache file path for design brief.
    
    Args:
        text: Input text to hash
        cache_dir: Directory for cache files
        
    Returns:
        Path to design brief cache file
    """
    text_hash = compute_text_hash(text)
    return cache_dir / f"design_brief_{text_hash}.json"


def load_design_brief_from_cache(text: str, cache_dir: Path) -> Optional[DesignBrief]:
    """
    Try to load cached design brief.
    
    Args:
        text: Input text (used for hash computation)
        cache_dir: Directory containing cache files
        
    Returns:
        DesignBrief if cache hit and valid, None otherwise
    """
    cache_path = get_design_brief_cache_path(text, cache_dir)
    
    if not cache_path.exists():
        logger.info("Design brief cache miss")
        return None
    
    try:
        logger.info("Design brief cache hit")
        cached_data = read_json_file(cache_path)
        design_brief = DesignBrief(**cached_data)
        logger.info("Design brief cache data is valid")
        return design_brief
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Design brief cache data is invalid: {e}. Will regenerate.")
        return None
    except Exception as e:
        logger.error(f"Error loading design brief cache: {e}", exc_info=True)
        return None


def save_design_brief_to_cache(text: str, design_brief: DesignBrief, cache_dir: Path):
    """
    Save design brief to cache.
    
    Args:
        text: Input text (used for hash computation)
        design_brief: Design brief data to cache
        cache_dir: Directory for cache files
    """
    cache_path = get_design_brief_cache_path(text, cache_dir)
    
    try:
        data_dict = design_brief.model_dump()
        write_json_file_atomic(cache_path, data_dict)
        logger.info(f"Saved design brief to cache: {cache_path}")
    except Exception as e:
        logger.error(f"Failed to save design brief cache: {e}", exc_info=True)


def get_image_prompt_cache_path(brief_json: str, cache_dir: Path) -> Path:
    """
    Generate cache file path for image prompt.
    
    Args:
        brief_json: JSON string of design brief
        cache_dir: Directory for cache files
        
    Returns:
        Path to image prompt cache file
    """
    text_hash = compute_text_hash(brief_json)
    return cache_dir / f"image_prompt_{text_hash}.txt"


def load_image_prompt_from_cache(brief_json: str, cache_dir: Path) -> Optional[str]:
    """
    Try to load cached image prompt.
    
    Args:
        brief_json: JSON string of design brief
        cache_dir: Directory containing cache files
        
    Returns:
        Prompt string if cache hit, None otherwise
    """
    cache_path = get_image_prompt_cache_path(brief_json, cache_dir)
    
    if not cache_path.exists():
        logger.info("Image prompt cache miss")
        return None
    
    try:
        logger.info("Image prompt cache hit")
        prompt = read_text_file(cache_path)
        prompt = " ".join(prompt.split())
        return prompt if prompt else None
    except Exception as e:
        logger.error(f"Error loading image prompt cache: {e}", exc_info=True)
        return None


def save_image_prompt_to_cache(brief_json: str, prompt: str, cache_dir: Path):
    """
    Save image prompt to cache.
    
    Args:
        brief_json: JSON string of design brief
        prompt: Prompt text to cache
        cache_dir: Directory for cache files
    """
    cache_path = get_image_prompt_cache_path(brief_json, cache_dir)
    
    try:
        cache_path.write_text(prompt, encoding="utf-8")
        logger.info(f"Saved image prompt to cache: {cache_path}")
    except Exception as e:
        logger.error(f"Failed to save image prompt cache: {e}", exc_info=True)


def make_image_prompt_from_brief(
    brief: DesignBrief,
    model: str,
    api_key: str,
    cache_dir: Path,
    use_cache: bool = True,
    max_retries: int = 2
) -> str:
    """
    Generate an image prompt from a design brief using OpenAI.
    
    Args:
        brief: DesignBrief data
        model: OpenAI model name
        api_key: OpenAI API key
        cache_dir: Directory for cache files
        use_cache: Whether to use cached results
        max_retries: Maximum number of retry attempts for invalid output
        
    Returns:
        Single-line prompt (<= 900 characters)
    """
    brief_json = json.dumps(brief.model_dump(), ensure_ascii=False, sort_keys=True)
    
    if use_cache:
        cached = load_image_prompt_from_cache(brief_json, cache_dir)
        if cached:
            return cached
    
    client = OpenAI(api_key=api_key)
    system_prompt = (
        "You are an expert visual prompt writer. "
        "Return a single-line image prompt with no explanations. "
        "Maximum length: 900 characters."
    )
    
    for attempt in range(1, max_retries + 2):
        try:
            logger.info(f"Requesting image prompt (attempt {attempt}/{max_retries + 1})")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": brief_json}
                ],
                temperature=0
            )
            prompt = response.choices[0].message.content
            prompt = " ".join(prompt.strip().split())
            
            if not prompt:
                raise ValueError("Empty prompt")
            if len(prompt) > 900:
                raise ValueError("Prompt exceeds 900 characters")
            
            if use_cache:
                save_image_prompt_to_cache(brief_json, prompt, cache_dir)
            
            logger.info("Image prompt generated successfully")
            return prompt
            
        except Exception as e:
            logger.warning(f"Failed to generate image prompt (attempt {attempt}): {e}")
            if attempt == max_retries + 1:
                raise

def call_openai_api(
    client: OpenAI,
    text: str,
    model: str,
    temperature: float
) -> str:
    """
    Make a call to OpenAI API.
    
    Args:
        client: OpenAI client instance
        text: Input transcript text
        model: Model name to use
        temperature: Temperature parameter
        
    Returns:
        Raw response text from the API
        
    Raises:
        OpenAIError: On API errors
    """
    system_prompt = f"""You are an expert analyst for client conversations.
Analyze the provided dialogue transcript and extract structured information.

You MUST respond with ONLY valid JSON, no additional text or explanations.
Use the following schema:

{REPORT_SCHEMA_DESCRIPTION}

Important:
- Extract the client's name from the dialogue
- Identify the main topic and primary request
- Analyze sentiment (positive/neutral/negative) and rate it 1-5
- Provide a concise summary
- List 3-7 key points discussed
- Suggest 2-5 concrete next steps
- Extract desired timeline/deadline if mentioned (or null if not)
- Extract budget/cost expectations if mentioned (or null if not)
- List core requirements - specific features/capabilities that MUST be in the final product
- Output ONLY the JSON object, nothing else"""

    user_prompt = f"""Analyze this client dialogue transcript:

{text}

Respond with ONLY valid JSON following the schema provided."""

    logger.debug(f"Calling OpenAI API with model {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )
    
    result = response.choices[0].message.content
    logger.debug(f"Received response: {len(result)} characters")
    
    return result


def parse_and_validate_response(response_text: str, attempt: int = 1) -> ReportData:
    """
    Parse and validate OpenAI response as JSON.
    
    Args:
        response_text: Raw response from API
        attempt: Current attempt number (for logging)
        
    Returns:
        Validated ReportData
        
    Raises:
        json.JSONDecodeError: If response is not valid JSON
        ValidationError: If JSON doesn't match schema
    """
    logger.debug(f"Parsing response (attempt {attempt})")
    
    # Try to extract JSON if wrapped in markdown code blocks
    text = response_text.strip()
    if text.startswith("```"):
        # Remove markdown code blocks
        lines = text.split('\n')
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = '\n'.join(lines)
    
    # Parse JSON
    data = json.loads(text)
    
    # Validate with Pydantic
    report_data = ReportData(**data)
    logger.info("Successfully parsed and validated response")
    
    return report_data


def call_openai_design_brief(
    client: OpenAI,
    text: str,
    model: str
) -> str:
    """
    Make a call to OpenAI API for design brief extraction.
    
    Args:
        client: OpenAI client instance
        text: Input transcript text
        model: Model name to use
        
    Returns:
        Raw response text from the API
    """
    system_prompt = f"""You are an expert design strategist.
Extract a design brief from the provided transcript.

You MUST respond with ONLY valid JSON, no additional text or explanations.
Use the following schema:

{DESIGN_BRIEF_SCHEMA_DESCRIPTION}

Important:
- Provide clear, concise strings
- All list fields must be arrays (can be empty if not mentioned)
- content_notes should be null if not mentioned
- Output ONLY the JSON object, nothing else"""

    user_prompt = f"""Extract a design brief from this transcript:

{text}

Respond with ONLY valid JSON following the schema provided."""

    logger.debug(f"Calling OpenAI API for design brief with model {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )
    
    result = response.choices[0].message.content
    logger.debug(f"Received design brief response: {len(result)} characters")
    
    return result


def parse_and_validate_design_response(response_text: str, attempt: int = 1) -> DesignBrief:
    """
    Parse and validate design brief response as JSON.
    
    Args:
        response_text: Raw response from API
        attempt: Current attempt number (for logging)
        
    Returns:
        Validated DesignBrief
        
    Raises:
        json.JSONDecodeError: If response is not valid JSON
        ValidationError: If JSON doesn't match schema
    """
    logger.debug(f"Parsing design brief response (attempt {attempt})")
    
    data = json.loads(response_text.strip())
    design_brief = DesignBrief(**data)
    logger.info("Successfully parsed and validated design brief")
    
    return design_brief


def extract_design_brief(
    text: str,
    model: str,
    api_key: str,
    cache_dir: Path,
    use_cache: bool = True,
    max_retries: int = 2
) -> DesignBrief:
    """
    Extract design brief from transcript using OpenAI API.
    
    Args:
        text: Transcript text to analyze
        model: OpenAI model name
        api_key: OpenAI API key
        cache_dir: Directory for cache files
        use_cache: Whether to use cached results
        max_retries: Maximum number of retry attempts for invalid JSON
        
    Returns:
        Validated DesignBrief
    """
    if use_cache:
        cached = load_design_brief_from_cache(text, cache_dir)
        if cached:
            return cached
    
    client = OpenAI(api_key=api_key)
    
    for attempt in range(1, max_retries + 2):
        try:
            logger.info(f"Requesting design brief (attempt {attempt}/{max_retries + 1})")
            start_time = time.time()
            
            response_text = call_openai_design_brief(client, text, model)
            
            elapsed = time.time() - start_time
            logger.info(f"Design brief API call completed in {elapsed:.2f}s")
            
            design_brief = parse_and_validate_design_response(response_text, attempt)
            
            if use_cache:
                save_design_brief_to_cache(text, design_brief, cache_dir)
            
            return design_brief
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse/validate design brief (attempt {attempt}): {e}")
            
            if attempt <= max_retries:
                logger.info("Asking AI to fix the design brief response...")
                correction_prompt = f"""The previous response was not valid JSON or didn't match the required schema.
Error: {str(e)}

Please provide ONLY valid JSON following this exact schema:
{DESIGN_BRIEF_SCHEMA_DESCRIPTION}

No explanations, no markdown formatting, just pure JSON."""
                
                try:
                    response_text = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": correction_prompt}
                        ],
                        temperature=0
                    ).choices[0].message.content
                    
                    design_brief = parse_and_validate_design_response(response_text, attempt)
                    
                    if use_cache:
                        save_design_brief_to_cache(text, design_brief, cache_dir)
                    
                    return design_brief
                    
                except Exception as retry_error:
                    logger.warning(f"Design brief retry {attempt} also failed: {retry_error}")
                    if attempt == max_retries:
                        raise
            else:
                logger.error("Exhausted all retries for valid design brief JSON response")
                raise
                
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
            logger.error(f"Unexpected error in design brief extraction: {e}", exc_info=True)
            raise

def process_dialog_with_ai(
    text: str,
    model: str,
    temperature: float,
    api_key: str,
    cache_dir: Path,
    use_cache: bool = True,
    max_retries: int = 2
) -> ReportData:
    """
    Process dialogue transcript with OpenAI API.
    
    Implements caching and retry logic for robustness.
    
    Args:
        text: Transcript text to analyze
        model: OpenAI model name
        temperature: Temperature parameter
        api_key: OpenAI API key
        cache_dir: Directory for cache files
        use_cache: Whether to use cached results
        max_retries: Maximum number of retry attempts for invalid JSON
        
    Returns:
        Validated ReportData
        
    Raises:
        Various exceptions on unrecoverable errors
    """
    # Check cache first
    if use_cache:
        cached = load_from_cache(text, cache_dir)
        if cached:
            return cached
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Try to get valid response
    for attempt in range(1, max_retries + 2):  # +2 because first is not a retry
        try:
            logger.info(f"Requesting AI analysis (attempt {attempt}/{max_retries + 1})")
            start_time = time.time()
            
            response_text = call_openai_api(client, text, model, temperature)
            
            elapsed = time.time() - start_time
            logger.info(f"API call completed in {elapsed:.2f}s")
            
            # Try to parse and validate
            report_data = parse_and_validate_response(response_text, attempt)
            
            # Success - save to cache
            if use_cache:
                save_to_cache(text, report_data, cache_dir)
            
            return report_data
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse/validate response (attempt {attempt}): {e}")
            
            if attempt <= max_retries:
                # Retry with correction prompt
                logger.info("Asking AI to fix the response...")
                correction_prompt = f"""The previous response was not valid JSON or didn't match the required schema.
Error: {str(e)}

Please provide ONLY valid JSON following this exact schema:
{REPORT_SCHEMA_DESCRIPTION}

No explanations, no markdown formatting, just pure JSON."""
                
                try:
                    response_text = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": correction_prompt}
                        ],
                        temperature=0
                    ).choices[0].message.content
                    
                    # Try to parse corrected response
                    report_data = parse_and_validate_response(response_text, attempt)
                    
                    if use_cache:
                        save_to_cache(text, report_data, cache_dir)
                    
                    return report_data
                    
                except Exception as retry_error:
                    logger.warning(f"Retry {attempt} also failed: {retry_error}")
                    if attempt == max_retries:
                        raise
            else:
                # No more retries
                logger.error("Exhausted all retries for valid JSON response")
                raise
                
        except APIConnectionError as e:
            logger.error(f"Network error connecting to OpenAI: {e}", exc_info=True)
            raise Exception(f"Network error: Unable to connect to OpenAI API. Check your internet connection.")
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}", exc_info=True)
            raise Exception(f"Rate limit exceeded. Please try again later or check your OpenAI plan.")
            
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}", exc_info=True)
            raise Exception(f"Request timed out. Please try again.")
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise Exception(f"OpenAI API error: {e.message if hasattr(e, 'message') else str(e)}")
            
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}", exc_info=True)
            raise Exception(f"OpenAI error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error in AI processing: {e}", exc_info=True)
            raise
