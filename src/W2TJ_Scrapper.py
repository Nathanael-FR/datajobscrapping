import datetime
import os
from selectolax.parser import HTMLParser
import time
import pandas as pd
from urllib.parse import urljoin
from typing import Generator
import re
from models import JobItem
from ScrapperInterface import Scrapper
from selenium import webdriver
import undetected_chromedriver as uc
from logger import Logger


class W2TJScrapper(Scrapper):

    BASE_URL: str = "https://www.welcometothejungle.com/fr/jobs?refinementList%5Boffices.country_code%5D%5B%5D=FR&query=data%20engineer%20senior&page={}&aroundQuery=France"

    def start_webdriver(self):

        print('starting Chrome Webdriver...')
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-features=NetworkService")
        options.add_argument("--disable-features=NetworkServiceInProcess")
        options.add_argument("--disable-features=IsolateOrigins")
        options.add_argument("--disable-features=site-per-process")

        self.driver = uc.Chrome(options=options)

    def close_webdriver(self):

        print('closing Chrome Webdriver...')

        self.driver.close()
        self.driver.quit()

    @staticmethod
    def get_max_jobs(html: HTMLParser) -> int:

        try:
            # div element whose data-testid attribute is 'jobs-search-results-count'
            total_jobs = html.css_first(
                "div[data-testid='jobs-search-results-count']").text(deep=True)
            return int(total_jobs)
        except Exception as e:
            print(f"Error extracting max jobs: {e}")
            return None

    @staticmethod
    def get_max_pages(html: HTMLParser) -> int:

        try:
            # Nav element whose aria-label attribute is 'Pagination'
            navbar = html.css_first("nav[aria-label='Pagination']")
            # Extract all a elements
            pages = navbar.css("a")
            return int(pages[-2].text(deep=True))
        except Exception as e:
            print(f"Error extracting max pages: {e}")
            return 1

    @staticmethod
    def extract_logo_url(html: HTMLParser, company_name: str) -> str:

        try:
            logo = html.css_first(f'img[alt="{company_name}"]')
            return logo.attributes['src']
        except Exception as e:
            print(f"Error extracting logo URL for {company_name}: {e}")
            return None

    def parse_page(self, html: HTMLParser) -> Generator[str, None, None]:

        job_urls = set([url.attributes["href"] for url in html.css(
            "a[href*='/fr/companies/']") if len(url.attributes["href"]) > 40])
        for job_url in job_urls:
            yield urljoin(self.BASE_URL, job_url)

    def parse_job_offer(self, job_offer_url: str) -> JobItem:

        html = self.get_html(job_offer_url)

        if not html:
            return None

        job_title = self.extract_text(
            html, 'h2[class="sc-gvZAcH lodDwl  wui-text"]')
        company_name = self.extract_text(
            html, 'span[class="sc-gvZAcH lpuzVS  wui-text"]')

        salary, remote = None, None
        job_details = html.css("div[class='sc-bOhtcR eDrxLt']")
        for detail in job_details:
            if detail.css_first("i[name='location']"):
                job_location = detail.text(deep=True)
            if detail.css_first("i[name='contract']"):
                contract_type = detail.text(deep=True)
            if detail.css_first("i[name='salary']"):
                salary = detail.text(deep=True)
            if detail.css_first("i[name='remote']"):
                remote = detail.text(deep=True)

        if html.css('span[class="sc-bOhtcR eDrxLt"]'):
            locations = html.css("span[class='q7vo0q-1 jubwAZ']")
            job_location = ", ".join([location.text(deep=True)
                                     for location in locations])

        publication_date = self.extract_text(html, 'time', attri='datetime')
        company_logo_url = self.extract_logo_url(html, company_name)

        company_sector = self.extract_text(
            html, 'div[data-testid="job-company-tag"] span')

        return JobItem(
            job_title=job_title,
            job_url=job_offer_url,
            company_name=company_name,
            location=job_location,
            contract_type=contract_type,
            salary=salary,
            remote=remote,
            publication_date=publication_date,
            company_logo_url=company_logo_url,
            company_sector=company_sector
        )

    def run(self, filename: str):

        data = []
        try:
            self.start_webdriver()

            html = self.get_html(self.BASE_URL, page=1, webdriver=self.driver)
            max_jobs = self.get_max_jobs(html)
            max_pages = self.get_max_pages(html)
            logger.info(f"Found {max_jobs} job offers on {max_pages} page(s)")

            for page in range(1, max_pages + 1):
                html = self.get_html(
                    self.BASE_URL, page=page, webdriver=self.driver)
                if not html:
                    break
                job_urls = self.parse_page(html)
                for url in job_urls:
                    job_item = self.parse_job_offer(url)
                    logger.info(f"Processing job offer: {url}")
                    if job_item:
                        self.logger.info(job_item.__dict__)
                        data.append(job_item.__dict__)
                    else:
                        print(f"Error while parsing job offer: {url}")
                    time.sleep(1)

            df = pd.DataFrame(data)
            logger.info(
                f"Scraped {len(df)} / {max_jobs} job offers. Saving to job_offers.csv...")
            df.to_csv(filename, index=False)

        finally:
            self.close_webdriver()


if __name__ == "__main__":

    today = datetime.date.today().strftime("%Y-%m-%d")
    logger = Logger(f"scrapping_{today}.log").get_logger()

    scrapper = W2TJScrapper()
    scrapper.run(filename=f"job_offers_W2TJ_{today}.csv")

    try:
        scrapper.load_to_s3(f"job_offers_W2TJ_{today}.csv")
        scrapper.load_to_s3(f"scrapping_{today}.log")
    except Exception as e:
        logger.error(f"Error loading to S3: {e}")
    else:
        os.remove(f"job_offers_W2TJ_{today}.csv")
        os.remove(f"scrapping_{today}.log")

    logger.info("*" * 50, "End of scrapping", "*" * 50)
