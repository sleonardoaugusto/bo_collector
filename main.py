import os
import time
from abc import ABC
from time import sleep
from typing import Union

import requests
from selenium.common import NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver

DOWNLOAD_DIR = 'downloads'


def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} created.")
    else:
        print(f"Directory {directory} already exists.")


class Driver:
    def __init__(self, options):
        self.webdriver = webdriver.Chrome(options=options)

    def __enter__(self) -> WebDriver:
        return self.webdriver

    def __exit__(self, type, value, traceback):
        self.webdriver.close()


class PageElement(ABC):
    def __init__(self, webdriver: WebDriver = None):
        self.webdriver = webdriver

    def find_element(self, locator: tuple[str, str]) -> WebElement:
        sleep(1)
        return self.webdriver.find_element(*locator)


class Page(PageElement, ABC):
    def __init__(self, webdriver: WebDriver, url: Union[str, None] = None):
        super().__init__(webdriver)
        self.url = url

    def open(self):
        print(f'Opening {self.url}')
        self.webdriver.get(self.url)


class Captcha:
    URL = 'http://2captcha.com/in.php'
    API_KEY = 'c260a06983e5fbdd5c3c18e9fb7d1699'

    def __init__(self, captcha_element: WebElement):
        self.captcha_element = captcha_element

    def download_image(self):
        print('Starting processing captcha image...')
        captcha_image = self.captcha_element.screenshot_as_png

        # Download the captcha image
        with open('captcha.png', 'wb') as f:
            f.write(captcha_image)

        return open("captcha.png", "rb")

    def solve(self, captcha_image):
        print("Starting 2captcha communication...")
        captcha_file = {'file': captcha_image}
        captcha_data = {'key': self.API_KEY, 'method': 'post'}
        captcha_response = requests.post(
            'http://2captcha.com/in.php', files=captcha_file, data=captcha_data
        )

        if captcha_response.text.split('|')[0] != 'OK':
            print('Error submitting captcha to 2Captcha')
            exit()

        captcha_id = captcha_response.text.split('|')[1]
        print(f'Communication successful! Captcha ID: {captcha_id}')

        # Wait for 2Captcha to solve the captcha
        time.sleep(5)  # Adjust the sleep time as needed

        # Get the solved captcha text
        token_url = (
            f"http://2captcha.com/res.php?key={self.API_KEY}&action=get&id={captcha_id}"
        )
        for i in range(20):  # Retry for up to 20 times with a 5-second interval
            print(f'Attempting to solve captcha {i+1} of 20...')
            time.sleep(5)
            response = requests.get(token_url)
            if response.text.split('|')[0] == 'OK':
                captcha_text = response.text.split('|')[1]
                print(f'Captcha solved successfully: {captcha_text}')
                return captcha_text
        else:
            print('Captcha solving failed')

    def solve_captcha(self):
        print('Starting solving captcha...')
        image = self.download_image()
        return self.solve(image)


class BOPM(Page):
    token_input = (By.ID, 'token')
    captcha_img = (By.XPATH, '//*[@id="conteudo"]/div/div[5]/div/div[1]/img')
    captcha_input = (By.ID, 'captcha')
    confirm_btn = (By.ID, 'btnConfirmar')
    error_dialog = (By.ID, 'ModalFlutuanteErro')

    def get_captcha(self):
        captcha = Captcha(self.find_element(self.captcha_img))
        return captcha.solve_captcha()

    def set_token(self, token):
        print(f'Entering token {token}')
        self.find_element(self.token_input).send_keys(token)

    def set_captcha(self, solved_captcha):
        print('Entering captcha')
        self.find_element(self.captcha_input).send_keys(solved_captcha)

    def click_confirm(self):
        print('Clicking confirm button')
        self.find_element(self.confirm_btn).click()

        if self.has_error():
            raise UnexpectedAlertPresentException

        time.sleep(10)

    def has_error(self):
        try:
            element = self.find_element(self.error_dialog)
            display_value = element.value_of_css_property('display')
            return display_value == 'block'
        except NoSuchElementException:
            print(f"Element with ID '{self.error_dialog[1]}' not found.")
            return False

    def download_pdf(self, token):
        self.open()

        self.set_token(token)
        self.set_captcha(self.get_captcha())

        try:
            self.click_confirm()
        except UnexpectedAlertPresentException:
            self.download_pdf(token)


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


ensure_directory_exists(DOWNLOAD_DIR)


with Driver(options=chrome_options) as driver:
    for token in [
        'BO201801011007330',
        'BO201801010811217',
        'BO201801010812840',
        'BO201801031008277',
        'BO201801030810702',
    ]:
        bopm = BOPM(driver, url='http://bopm.policiamilitar.sp.gov.br/')
        bopm.download_pdf(token)
