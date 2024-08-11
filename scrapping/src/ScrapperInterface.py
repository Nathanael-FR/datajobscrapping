from abc import ABC, abstractmethod
import re
from selectolax.parser import HTMLParser
from typing import Generator
import httpx
from dataclasses import dataclass, field

from unidecode import unidecode
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
from logger import Logger
from utils import scrape_prog_lang


@dataclass
class Scrapper(ABC):

    logger: Logger

    HEADERS: dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    })

    SKILLS: set[str] = field(default_factory=lambda: {
        "Python", "R", "SQL", "Java", "Scala", "Julia", "SAS", "MATLAB", "Ruby", "JavaScript",
        "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Scikit-learn",
        "TensorFlow", "Keras", "PyTorch", "NLTK", "spaCy", "Statsmodels",
        "Plotly", "Bokeh", "Dask", "XGBoost", "LightGBM", "CatBoost",
        "Hugging Face Transformers", "OpenCV", "FastAI", "Tableau", "Power BI",
        "QlikView", "Looker", "D3.js", "Grafana", "Metabase", "Superset",
        "Google Data Studio", "MySQL", "PostgreSQL", "SQLite",
        "Microsoft SQL Server", "MySQL", "Oracle Database", "IBM Db2",
        "MariaDB", "MongoDB", "Cassandra", "Redis", "CouchDB", "Neo4j",
        "Amazon DynamoDB", "HBase", "Couchbase", "Hadoop", "Apache", "Spark",
        "Kafka", "Flink", "Storm", "Samza", "Google BigQuery",
        "Amazon Redshift", "Snowflake", "Synapse Analytics", "Databricks",
        "NiFi", "Talend", "Informatica", "SSIS", "Pentaho", "Alteryx",
        "Airflow", "Stitch", "Fivetran", "Luigi", "AWS", "S3", "EC2", "EMR",
        "Redshift", "Athena", "Azure", "Data Lake", "SQL Database",
        "Databricks", "Synapse Analytics", "GCP", "BigQuery", "Dataflow",
        "Dataproc", "Pub/Sub", "Tableau", "Power BI", "QlikView", "Looker",
        "Domo", "Sisense", "MicroStrategy", "Jira", "Trello", "Asana",
        "Monday.com", "Basecamp", "ClickUp", "Git", "GitHub", "GitLab",
        "Bitbucket", "MLflow", "Kubeflow", "TFX", "Seldon", "ModelDB",
        "Docker", "Kubernetes", "Prefect", "DVC", "Great Expectations", "dbt"
    })

    def get_html(self, baseurl, webdriver: ChromeDriver = None, **kwargs) -> HTMLParser:

        url = baseurl

        if kwargs.get("page"):
            page = kwargs.get("page")
            url = baseurl.format(page)

        if not webdriver:
            try:
                resp = httpx.get(url, headers=self.HEADERS)
            except TimeoutError as t:
                self.logger.error(
                    f"Timeout while requesting {url}: {t}")
                raise t
            except Exception as e:
                self.logger.error(
                    f"Error while requesting {url}: {e}")
                return None
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
            return None

    @ abstractmethod
    def get_max_jobs(self) -> int | None: ...

    @ abstractmethod
    def get_max_pages(self) -> int: ...

    @ abstractmethod
    def parse_page(self) -> Generator: ...

    @ abstractmethod
    def parse_job_offer(self) -> JobItem: ...

    @ abstractmethod
    def process_salary(self, salary: str) -> str: ...

    @ staticmethod
    def process_job_title(title: str) -> str:
        """Clean job title from unwanted characters."""

        pattern = r"\([A-Za-z]/[A-Za-z]/[A-Za-z]\)"
        pattern2 = r"[A-Za-z]/[A-Za-z]/[A-Za-z]"
        pattern3 = r"\([A-Za-z]/[A-Za-z]\)"
        pattern4 = r"[A-Za-z]/[A-Za-z]"
        pattern5 = r"[A-Za-z] - [A-Za-z] - [A-Za-z]"
        pattern6 = r"[A-Za-z] - [A-Za-z]"

        title = re.sub(pattern, "", title)
        title = re.sub(pattern2, "", title)
        title = re.sub(pattern3, "", title)
        title = re.sub(pattern4, "", title)
        title = re.sub(pattern5, "", title)
        title = re.sub(pattern6, "", title)

        return unidecode(
            title.replace("(/)", "")
            .replace("-", "")
            .replace("CDI", "")
            .strip()
            .lower()
        )

    @staticmethod
    def process_remote(remote: str) -> str:
        if remote:
            if "occasionnel" in remote:
                return "occasionnel"
            elif "partiel" in remote:
                return "partiel"
            elif "complet" in remote:
                return "total"

    @staticmethod
    def process_contract_type(job_type: str) -> str:

        job_type = job_type.lower()
        if "stage" in job_type:
            return "stage"

        return job_type

    def get_skills_desc(self, job_desc: str) -> list[str]:
        """ Retrieve skills mentionned in job description. """

        words = set(job_desc.split())
        skills_mentionned = self.SKILLS.intersection(words)
        return list(skills_mentionned)

    def get_skills_title(self, job_title: str) -> list[str]:
        """ Retrieve skills & programming lang mentionned in job title. """

        langs = scrape_prog_lang()
        words = set(job_title.split())
        langs_mentionned = set(langs).intersection(words)
        skills_mentionned = self.SKILLS.intersection(words)
        return list(langs_mentionned) + list(skills_mentionned)

    def process_df(self, df: pd.DataFrame) -> pd.DataFrame:

        df["skills"] = df["job_description"].apply(
            lambda x: self.get_skills_desc(x)) + df["job_title"].apply(
                lambda x: self.get_skills_title(x))

        df["salary"] = df["salary"].apply(lambda x: self.process_salary(x))
        df["remote_type"] = df["remote_type"].apply(lambda x: self.process_remote(x))
        df["contract_type"] = df["contract_type"].apply(
            lambda x: self.process_contract_type(x))
        df["job_title"] = df["job_title"].apply(
            lambda x: self.process_job_title(x))

        return df

    def load_to_s3(self, filename: str) -> None:

        session = boto3.Session(
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        )

        client = session.client('s3')

        folder = "data" if ".csv" in filename else "logs"
        client.upload_file(
            filename, os.environ['S3_BUCKET_NAME'], f'{folder}/{filename}')

    @abstractmethod
    def run(self, filename: str) -> None: ...
