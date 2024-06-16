# Load environment variables from .env file
import os

from dotenv import load_dotenv

load_dotenv()

DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', 'downloads')
BOPM_URL = os.getenv('BOPM_URL')
API_KEY = os.getenv('API_KEY')
