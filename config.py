"""
Configuration module for AI Client Report Generator.
Loads environment variables and validates required settings.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0"))
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL") or "gpt-image-1"
OPENAI_IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE") or "1024x1024"

# Paths
CACHE_DIR = PROJECT_ROOT / os.getenv("CACHE_DIR", "cache/ai_outputs")
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Ensure required directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def validate_config():
    """Validate that all required configuration is present."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not set in environment variables.")
        print("Please copy .env.example to .env and fill in your API key.")
        sys.exit(1)
    
    if not OPENAI_API_KEY.startswith("sk-"):
        print("WARNING: OPENAI_API_KEY does not look like a valid OpenAI API key.")
        print("Make sure you've set the correct key in your .env file.")
