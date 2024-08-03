import pytest
import pandas as pd
from scrapping.src.models import JobItemProcessed
import sys
import os


class TestS3ToDB:

    @staticmethod
    def TestFromCSVtoJobItem():

        dummy_job_offers = pd.DataFrame({
            'job_title': ['Data Scientist', 'Data Engineer'],
            'company': ['Google', 'Facebook'],
            'location': ['Paris', 'Lyon'],
            'salary': ['1000', '2000'],
            'contract_type': ['CDI', 'CDD'],
            'remote': ['partiel', 'complet'],
            'job_description': ['description1', 'description2'],
            'skills': [['python', 'sql'], ['java', 'scala']]
        })

        for _, row in dummy_job_offers.iterrows():
            job_offer: dict = row.to_dict()
            job = JobItemProcessed(**job_offer)

            assert job is not None
