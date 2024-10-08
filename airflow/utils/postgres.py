import psycopg2
from utils.models import JobItemProcessed
from datetime import datetime


def get_conn():
    try:
        conn = psycopg2.connect(
            dbname="webscrapper",
            user="postgres",
            password="postgres",
            host="postgres",
        )
    except Exception as e:
        return
    else:
        return conn


def insert_job_offer(conn, job_offer: JobItemProcessed):

    if job_offer.job_description:
        if job_offer.job_description.startswith('"'):
            job_offer.job_description = job_offer.job_description[1:-1]

    job_offer.publication_date = datetime.strptime(
        job_offer.publication_date, "%d/%m/%Y").strftime("%Y-%m-%d")

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            INSERT INTO joboffers(
            job_title, job_url, job_desc, salary, company_name, company_sector,
            company_logo_url, loc, contract_type, remote_type, publication_date, skills
            ) VALUES (
            '{job_offer.job_title}', '{job_offer.job_url}', '{job_offer.job_description}',
            '{job_offer.salary}', '{job_offer.company_name}', '{job_offer.company_sector}',
            '{job_offer.company_logo_url}', '{job_offer.location}', '{job_offer.contract_type}',
            '{job_offer.remote_type}', '{job_offer.publication_date}', '{job_offer.skills}'
            )
            """
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    else:
        print("Data inserted successfully")
    finally:
        cursor.close()


if __name__ == "__main__":

    """ Test the connection to the database and insert dummy data then delete it """

    conn = get_conn()
    if conn:
        print("Connected to the database")
        insert_job_offer(
            conn,
            JobItemProcessed(
                job_title="Data Engineer",
                job_url="https://www.data-engineer.com",
                job_description="Data Engineer job description",
                salary="50000",
                company_name="Data Engineer Company",
                company_sector="Data Engineering",
                company_logo_url="https://www.data-engineer.com/logo",
                location="Paris",
                contract_type="CDI",
                remote_type="No remote",
                publication_date="2021-01-01",
                skills="Python, SQL, ETL",
            ),
        )
        cursor = conn.cursor()
        # remove the inserted data (last row)
        cursor.execute(
            "DELETE FROM joboffers WHERE company_name='Data Engineer Company'")
        conn.commit()
        cursor.close()
        conn.close()
