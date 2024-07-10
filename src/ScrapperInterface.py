from abc import ABC, abstractmethod
from selectolax.parser import HTMLParser
from typing import Generator
import httpx
from dataclasses import dataclass, field
from models import JobItem
import time
import pandas as pd
import undetected_chromedriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import boto3
import os
from dotenv import load_dotenv
from logger import Logger


@dataclass
class Scrapper(ABC):

    logger: Logger

    HEADERS: dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    })

    def get_html(self, baseurl, webdriver: ChromeDriver = None, **kwargs) -> HTMLParser:

        url = baseurl

        if kwargs.get("page"):
            page = kwargs.get("page")
            url = baseurl.format(page)

        if not webdriver:
            resp = httpx.get(url, headers=self.HEADERS)
        else:
            webdriver.get(url)
            self.accept_cookies(webdriver)

        try:
            resp.raise_for_status()

        except httpx.HTTPStatusError as e:
            self.self.logger.error(
                f"Error response {resp.status_code} while requesting {e.request.url!r}")
        except UnboundLocalError:
            return HTMLParser(webdriver.page_source)
        else:
            return HTMLParser(resp.text)

    def accept_cookies(self, driver: ChromeDriver):
        """Accept cookies if the button is present on the page."""

        try:
            cookies = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
            cookies.click()
        except:
            pass

    def extract_text(self, element: HTMLParser, sel: str, **kwargs) -> str:

        attribute = kwargs.get("attri")
        try:
            if attribute:
                return element.css_first(sel).attributes[attribute].strip()
            else:
                return element.css_first(sel).text(deep=True).strip()
        except Exception as e:

            self.logger.error(f"{e}. Error extracting text from {sel}")
            raise e

    @abstractmethod
    def get_max_jobs(self) -> int | None: pass

    @abstractmethod
    def get_max_pages(self) -> int: pass

    @abstractmethod
    def parse_page(self) -> Generator: pass

    @abstractmethod
    def parse_job_offer(self) -> JobItem: pass

    def load_to_s3(self, filename: str) -> None:

        session = boto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        client = session.client('s3')

        folder = "data/" if ".csv" in filename else "logs/"
        client.upload_file(filename, os.getenv(
            'S3_BUCKET_NAME'), f'{folder}/{filename}')

    def run(self, filename: str):

        data = []

        html = self.get_html(self.BASE_URL, page=1)
        max_pages = self.get_max_pages(html)
        max_jobs = self.get_max_jobs(html)
        self.logger.info(f"Found {max_jobs} job offers on {max_pages} page(s)")

        for page in range(1, max_pages + 1):
            html = self.get_html(self.BASE_URL, page=page)
            if not html:
                break

            job_urls = self.parse_page(html)
            for url in job_urls:
                self.logger.info(f"Processing job offer: {url}")
                job_item = self.parse_job_offer(url)
                if job_item:
                    self.logger.info(job_item.__dict__)
                    data.append(job_item.__dict__)
                else:
                    self.logger.error(f"Error while parsing job offer: {url}")
                time.sleep(1)

        df = pd.DataFrame(data)
        self.logger.info(
            f"Scraped {len(df)} / {max_jobs} job offers. Saving to csv...")
        today = datetime.date.today()
        df.to_csv(filename, index=False)
