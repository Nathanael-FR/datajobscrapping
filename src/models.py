from dataclasses import dataclass

@dataclass
class JobItem:
    job_title: str | None
    job_url: str | None
    salary: str | None
    company_name: str | None
    company_sector: str | list[str] | None 
    company_logo_url: str | None
    location: str | None
    contract_type: str | None
    remote: str | None
    publication_date: str | None

