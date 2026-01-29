"""
Input/Output utilities.
Handles file reading/writing with proper error handling.
"""
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def read_text_file(file_path: Path) -> str:
    """
    Read text file with error handling.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Content of the file as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file cannot be decoded as text
    """
    try:
        logger.info(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully read {len(content)} characters from {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading file {file_path}: {e}", exc_info=True)
        raise


def read_json_file(file_path: Path) -> dict:
    """
    Read and parse JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        logger.debug(f"Reading JSON file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully parsed JSON from {file_path}")
        return data
    except FileNotFoundError:
        logger.debug(f"JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading JSON {file_path}: {e}", exc_info=True)
        raise


def write_json_file_atomic(file_path: Path, data: dict):
    """
    Write JSON to file atomically (using temp file + rename).
    
    Args:
        file_path: Path where to write the file
        data: Dictionary to serialize as JSON
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=file_path.parent,
            delete=False,
            suffix='.tmp'
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp_file.name)
        
        # Atomic rename
        tmp_path.replace(file_path)
        logger.debug(f"Successfully wrote JSON to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to write JSON to {file_path}: {e}", exc_info=True)
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and tmp_path.exists():
            tmp_path.unlink()
        raise


def get_cache_path(text_hash: str, cache_dir: Path) -> Path:
    """
    Generate cache file path for given text hash.
    
    Args:
        text_hash: SHA256 hash of the input text
        cache_dir: Directory for cache files
        
    Returns:
        Path to cache file
    """
    return cache_dir / f"{text_hash}.json"
