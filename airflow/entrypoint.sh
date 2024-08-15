#!/bin/bash
set -e

if [ -e "/opt/airflow/requirements.txt" ]; then
  $(command -v python) -m pip install --upgrade pip
  $(command -v pip) install -r /opt/airflow/requirements.txt
fi

# cd into the airflow directory and pip install -e . to install the app modules
cd /opt/airflow

if [ -e "/opt/airflow/setup.py" ]; then
  $(command -v pip) install -e .
fi

if [ ! -f "/opt/airflow/airflow.db" ]; then
  airflow db migrate && \
  airflow users create \
    --username admin \
    --firstname admin \
    --lastname admin \
    --role Admin \
    --email admin@example.com \
    --password admin
fi

$(command -v airflow) db migrate

exec "$@"
