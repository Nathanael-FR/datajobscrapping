from dataclasses import dataclass


@dataclass
class JobItem:
    job_title: str | None
    job_url: str | None
    job_description: str | None
    salary: str | None
    company_name: str | None
    company_sector: str | list[str] | None
    company_logo_url: str | None
    location: str | None
    contract_type: str | None
    remote_type: str | None
    publication_date: str | None

    def __str__(self) -> str:
        # Tronque la description à 50 caractères
        description = self.job_description[:50] + \
            "..." if self.job_description else None
        return f"Job title: {self.job_title}  | " + \
            f"Company: {self.company_name} | " \
            f"Location: {self.location} | " \
            f"Salary: {self.salary} | " \
            f"Remote: {self.remote_type} | " \
            f"Publication date: {self.publication_date} | " \
            f"Description: {description}"

    def __repr__(self) -> str:
        pass


@dataclass
class JobItemProcessed(JobItem):
    skills: list[str] | None
