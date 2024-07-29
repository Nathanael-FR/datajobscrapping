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
from logger import Logger


class HelloWorkScrapper(Scrapper):

    BASE_URL: str = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=Data+analyst+senior&k_autocomplete=&l=France&l_autocomplete=&p={}"

    COMPANY_FIELDS: list[str] = [
        "Agriculture • Pêche", "BTP", "Banque • Assurance • Finance", "Distribution • Commerce de gros",
        "Enseignement • Formation", "Immobilier", "Industrie Agro-alimentaire", "Industrie Auto • Meca • Navale",
        "Industrie Aéronautique • Aérospatial", "Industrie Manufacturière", "Industrie Pharmaceutique • Biotechn. • Chimie",
        "Industrie Pétrolière • Pétrochimie", "Industrie high-tech • Telecom", "Média • Internet • Communication",
        "Restauration", "Santé • Social • Association", "Secteur Energie • Environnement", "Secteur informatique • ESN",
        "Service public autres", "Service public d'état", "Service public des collectivités territoriales",
        "Service public hospitalier", "Services aux Entreprises", "Services aux Personnes • Particuliers",
        "Tourisme • Hôtellerie • Loisirs", "Transport • Logistique"
    ]

    @staticmethod
    def get_max_jobs(html: HTMLParser) -> int:

        try:
            total_jobs: str = html.css_first(
                "button[data-cy='offerNumberButton']").text(deep=True)
            return int(re.search(r"\d+", total_jobs).group())
        except Exception as e:
            logger.error(f"Error extracting max jobs: {e}")
            return None

    @staticmethod
    def get_max_pages(html: HTMLParser) -> int:

        try:
            navbar = html.css_first(
                "nav.tw-flex.tw-gap-2.tw-typo-m.tw-flex-wrap")
            pages = navbar.css("button")
            return int(pages[-2].text(deep=True))
        except Exception as e:
            logger.error(f"Error extracting max pages: {e}")
            return 1

    @staticmethod
    def extract_logo_url(html: HTMLParser, company_name: str) -> str:

        try:
            logo = html.css_first(f'img[alt="{company_name} recrutement"]')
            return logo.attributes['src']
        except Exception as e:
            logger.error(f"Error extracting logo URL for {company_name}: {e}")
            return None

    def parse_page(self, html: HTMLParser) -> Generator[str, None, None]:

        job_urls = html.css("a[href*='/fr-fr/emplois/']")
        for job_url in job_urls:
            yield urljoin(self.BASE_URL, job_url.attributes["href"])

    def parse_job_offer(self, job_offer_url: str) -> JobItem:

        html = self.get_html(job_offer_url)
        if not html:
            return None

        try:
            job_title = self.extract_text(html, "span[data-cy='jobTitle']")

            location_and_contract = html.css(
                "li.tw-tag-grey-s.tw-readonly")
            if location_and_contract:
                job_location = location_and_contract[0].text(
                    deep=True).strip() if len(location_and_contract) > 0 else None
                contract_type = location_and_contract[1].text(
                    deep=True).strip() if len(location_and_contract) > 1 else None
            else:
                job_location, contract_type = None, None

            company_name = self.extract_text(
                html, "span.tw-contents.tw-typo-m.tw-text-grey")
            salary = self.extract_text(html, "li.tw-tag-attractive-s.tw-readonly") if html.css_first(
                "li.tw-tag-attractive-s.tw-readonly") else None
            remote = self.extract_text(html, "li.tw-tag-primary-s.tw-readonly") if html.css_first(
                "li.tw-tag-primary-s.tw-readonly") else None

            if remote and "Télétravail" not in remote:
                remote = None

            job_tags = html.css(
                "li.tw-block.tw-tag-primary-s.tw-readonly.tw-w-fit.tw-whitespace-nowrap.tw-text-ellipsis.tw-overflow-hidden")
            company_sector = " • ".join(tag.text(deep=True).strip(
            ) for tag in job_tags if tag.text(deep=True).strip() in self.COMPANY_FIELDS)

            company_logo_url = self.extract_logo_url(html, company_name)

            date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")
            publication_date = date_pattern.search(self.extract_text(
                html, "span.tw-block.tw-typo-xs.tw-text-grey.tw-mt-3.tw-break-words"))
            publication_date = publication_date.group() if publication_date else None

            job_desc_sections = html.css(
                "p[class='tw-typo-long-m tw-mb-12 sm:tw-mb-14 tw-break-words']")

            job_description = " ".join(
                section.text(deep=True).strip() for section in job_desc_sections)

        except Exception as e:
            self.logger.error(f"Error parsing job offer: {e}")
            return None

        else:
            return JobItem(
                job_title=job_title,
                job_url=job_offer_url,
                job_description=job_description,
                salary=salary,
                company_name=company_name,
                company_sector=company_sector,
                company_logo_url=company_logo_url,
                location=job_location,
                contract_type=contract_type,
                remote=remote,
                publication_date=publication_date
            )

    @staticmethod
    def process_salary(salary: str | None) -> str:

        if salary:
            salary = salary.strip()\
                .replace("\xa0", " ")\
                .replace("\u202f", " ")

            if "mois" in salary:
                sal_low, sal_high = salary.split(" ")[0], salary.split(" ")[2]

                return f'{float(sal_low.replace(",","."))*12} - {float(sal_high.replace(",","."))*12} EUR par an'

            return salary

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
                    self.logger.info(job_item.__str__())
                    data.append(job_item.__dict__)
                else:
                    self.logger.error(f"Error while parsing job offer: {url}")
                time.sleep(1)

        df = pd.DataFrame(data)
        self.logger.info("Processing data...")
        df = self.process_df(df)
        self.logger.info(
            f"Scraped {len(df)} / {max_jobs} job offers. Saving to csv...")
        df.to_csv(filename, index=False)


if __name__ == "__main__":
    today = datetime.date.today().strftime("%Y-%m-%d")
    logger = Logger(f"scrapping_{today}.log").get_logger()

    scrapper = HelloWorkScrapper(logger)
    scrapper.run(filename=f"job_offers_HW_{today}.csv")

    try:
        scrapper.load_to_s3(f"job_offers_HW_{today}.csv")
        scrapper.load_to_s3(f"scrapping_{today}.log")
    except Exception as e:
        logger.error(f"Error loading to S3: {e}")
    else:
        os.remove(f"job_offers_HW_{today}.csv")
        os.remove(f"scrapping_{today}.log")

    logger.info("*" * 50 + "End of scrapping" + "*" * 50)
