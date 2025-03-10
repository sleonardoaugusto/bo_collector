# Load environment variables from .env file
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Define the DOWNLOAD_DIR path, resolving to an absolute path for clarity
_DOWNLOAD_DIR = (
    Path(__file__).parent / os.getenv("DOWNLOAD_DIR", "downloads")
).resolve()
# Convert to string if needed elsewhere (e.g., for JSON serialization or logging)
DOWNLOAD_DIR = str(_DOWNLOAD_DIR)

BOPM_URL = os.getenv("BOPM_URL")
CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")
