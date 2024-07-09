FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y cron

# Combine cron jobs into a single file
RUN echo "0 0 * * * python /app/src/HW_Scrapper.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/scrapper_cron
RUN echo "0 0 * * * python /app/src/W2TJ_Scrapper.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/scrapper_cron

RUN chmod 0644 /etc/cron.d/scrapper_cron

# Load the cron jobs into the crontab
RUN crontab /etc/cron.d/scrapper_cron
RUN touch /var/log/cron.log

# Start the cron service and log the output
CMD cron && tail -f /var/log/cron.log
