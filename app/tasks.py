from selenium.webdriver.chrome.options import Options
from selenium import webdriver

from app.celery_config import app
from app.constants import BOPM_URL
from app.main import BOPM, ensure_directory_exists, DOWNLOAD_DIR, logger

chrome_options = Options()
chrome_options.add_experimental_option(
    'prefs',
    {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
    },
)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

ensure_directory_exists(DOWNLOAD_DIR)


@app.task
def process_token(token):
    try:
        with webdriver.Chrome(options=chrome_options) as driver:
            logger.info(f"Processing token: {token}")
            bopm = BOPM(driver, url=BOPM_URL)
            bopm.download_pdf(token)
        logger.info(f"Completed processing token: {token}")
    except Exception as e:
        logger.error(f"Error processing token {token}: {str(e)}")
