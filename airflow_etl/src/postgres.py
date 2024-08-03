import psycopg2
import os
from scrapping.src.models import JobItem


def get_conn():
    try:
        conn = psycopg2.connect(
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host="postgres",
        )
    except Exception as e:
        print(e)
        return None
    else:
        return conn


def insert_job_offer(conn, job_offer: JobItem):
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO joboffers (title, company, location, salary, description, url) VALUES (%s, %s, %s, %s, %s, %s)",
        (job_offer.job_title, job_offer.company_name, job_offer.location, job_offer.salary, job_offer.job_description,
            job_offer.job_url)
    )
    conn.commit()
    cursor.close()
