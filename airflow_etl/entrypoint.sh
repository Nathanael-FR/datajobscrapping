#!/bin/bash
set -e

export PYTHONPATH=/opt/airflow/src:/opt/airflow/dags:$PYTHONPATH

if [ -e "/opt/airflow/requirements.txt" ]; then
  $(command -v python) -m pip install --upgrade pip
  $(command -v pip) install -r /opt/airflow/requirements.txt
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
