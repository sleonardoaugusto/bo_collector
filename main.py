import os
import time
from abc import ABC
from time import sleep
from typing import Union
import logging
import requests
from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver

from constants import CAPTCHA_API_KEY, DOWNLOAD_DIR, BOPM_URL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class InvalidTokenException(WebDriverException):
    """Thrown when then token is invalid."""


class InvalidCaptchaException(WebDriverException):
    """Thrown when the captcha is invalid."""


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    else:
        logger.info(f"Directory already exists: {directory}")


class Driver:
    def __init__(self, options):
        service = Service(executable_path="/usr/local/bin/chromedriver")
        self.webdriver = webdriver.Chrome(
            service=service,
            options=options
        )

    def __enter__(self) -> WebDriver:
        return self.webdriver

    def __exit__(self, type, value, traceback):
        self.webdriver.close()
        logger.info("WebDriver closed")


class PageElement(ABC):
    def __init__(self, webdriver: WebDriver = None):
        self.webdriver = webdriver

    def find_element(self, locator: tuple[str, str]) -> WebElement:
        sleep(1)
        element = self.webdriver.find_element(*locator)
        logger.info(f"Found element with locator: {locator}")
        return element


class Page(PageElement, ABC):
    def __init__(self, webdriver: WebDriver, url: Union[str, None] = None):
        super().__init__(webdriver)
        self.url = url

    def open(self):
        self.webdriver.get(self.url)
        logger.info(f"Opened URL: {self.url}")


class Captcha:
    URL = 'http://2captcha.com/in.php'

    def __init__(self, captcha_element: WebElement):
        self.captcha_element = captcha_element

    def download_image(self):
        captcha_image = self.captcha_element.screenshot_as_png

        with open('captcha.png', 'wb') as f:
            f.write(captcha_image)

        logger.info("Downloaded captcha image")
        return open("captcha.png", "rb")

    def solve(self, captcha_image):
        captcha_file = {'file': captcha_image}
        captcha_data = {'key': CAPTCHA_API_KEY, 'method': 'post'}
        captcha_response = requests.post(
            'http://2captcha.com/in.php', files=captcha_file, data=captcha_data
        )

        if captcha_response.text.split('|')[0] != 'OK':
            logger.error("Captcha solving failed")
            exit()

        captcha_id = captcha_response.text.split('|')[1]

        # Wait for 2Captcha to solve the captcha
        time.sleep(7)  # Adjust the sleep time as needed

        # Get the solved captcha text
        token_url = (
            f"http://2captcha.com/res.php?key={CAPTCHA_API_KEY}&action=get&id={captcha_id}"
        )
        for i in range(20):  # Retry for up to 20 times with a 5-second interval
            response = requests.get(token_url)

            if response.text.split('|')[0] == 'OK':
                captcha_text = response.text.split('|')[1]
                logger.info("Captcha solved")
                return captcha_text

            time.sleep(3)

        logger.error("Captcha solving timed out")

    def solve_captcha(self):
        image = self.download_image()
        return self.solve(image)


class BOPM(Page):
    token_input = (By.ID, 'token')
    captcha_img = (By.XPATH, '//*[@id="conteudo"]/div/div[5]/div/div[1]/img')
    captcha_input = (By.ID, 'captcha')
    confirm_btn = (By.ID, 'btnConfirmar')
    error_dialog = (By.ID, 'ModalFlutuanteErro')
    error_message = (By.XPATH, '//*[@id="ModalFlutuanteErro"]/div/div[2]/h3/span')

    def get_captcha(self):
        captcha = Captcha(self.find_element(self.captcha_img))
        return captcha.solve_captcha()

    def set_token(self, token):
        self.find_element(self.token_input).send_keys(token)
        logger.info(f"Set token: {token}")

    def set_captcha(self, solved_captcha):
        self.find_element(self.captcha_input).send_keys(solved_captcha)
        logger.info(f"Set captcha: {solved_captcha}")

    def wait_for_download(self, token):
        filename = f'{token}.pdf'

        def check_file():
            return os.path.isfile(os.path.join(DOWNLOAD_DIR, filename))

        # Loop to check the file every 5 seconds
        waited_for = 0
        interval = 5
        timeout = 90

        while True:
            if check_file():
                print(f"{filename} found in directory.")
                logger.info(f"Completed PDF download for token: {token}")
                break

            if waited_for > timeout:
                logger.error(f"{filename} download time out")
                break

            print(f"{filename} not found. Checking again in {interval} seconds.")

            waited_for += interval
            time.sleep(interval)

    def click_confirm(self):
        self.find_element(self.confirm_btn).click()
        logger.info("Clicked confirm button")

        self.validate()

    def validate(self):
        element = self.find_element(self.error_dialog)
        display_value = element.value_of_css_property('display')

        if display_value == 'block':
            logger.error("Error dialog present after clicking confirm")
            error_text = self.find_element(self.error_message).text

            if (
                "Não há registro eletrônico de ocorrência para o token informado!"
                or "Token inválido!" in error_text
            ):
                raise InvalidTokenException

            if "Captcha inválido" in error_text:
                raise InvalidCaptchaException

            logger.info(f"No relevant error messages found, {error_text}")

    def download_pdf(self, token, retry_count=3):
        self.open()
        self.set_token(token)
        self.set_captcha(self.get_captcha())

        try:
            self.click_confirm()
            self.wait_for_download(token)

        except InvalidCaptchaException:
            logger.error("Captcha is invalid, retrying...")
            self.download_pdf(token)

        except InvalidTokenException:
            if retry_count > 0:
                logger.error("Token invalid, retrying...")
                self.download_pdf(token, retry_count=retry_count - 1)
            else:
                logger.error(f"Token {token} invalid, attempts exhausted.")


chrome_options = Options()
chrome_options.add_experimental_option(
    'prefs',
    {
        "download.default_directory": DOWNLOAD_DIR,  # Change default directory for downloads
        "download.prompt_for_download": False,  # To auto download the file
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,  # Disable safe browsing checks
    },
)
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument(
    "--disable-dev-shm-usage"
)  # Overcome limited resource problems
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
chrome_options.binary_location = "/usr/bin/google-chrome"


ensure_directory_exists(DOWNLOAD_DIR)

with Driver(options=chrome_options) as driver:
    with open('tokens.txt', 'r') as f:
        rows = f.readlines()
        counter = 1

        for content in rows:
            start_time = time.time()
            print(f"Processing {counter} of {len(rows)}...")

            token = content.strip()

            bopm = BOPM(driver, url=BOPM_URL)
            logger.info(f"Starting PDF download for token: {token}")
            bopm.download_pdf(token)

            counter += 1

            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time: {execution_time} seconds")
