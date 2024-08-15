
CREATE TABLE IF NOT EXISTS joboffers (
    id      SERIAL      PRIMARY KEY,
    job_title           VARCHAR(255),
    job_url             VARCHAR(255),
    job_desc            TEXT,
    salary              VARCHAR(255),
    company_name        VARCHAR(255),
    company_sector      VARCHAR(255),
    company_logo_url    VARCHAR(255),
    loc                 VARCHAR(255),
    contract_type       VARCHAR(255),
    remote_type         VARCHAR(255),
    publication_date    DATE,
    skills              VARCHAR(255)
);