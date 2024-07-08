FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y cron

RUN echo "0 0 * * * python /app/src/HW_Scrapper.py >> /var/log/cron.log 2>&1" > /etc/cron.d/hw_scrapper_cron
RUN echo "0 0 * * * python /app/src/W2TJ_Scrapper.py >> /var/log/cron.log 2>&1" > /etc/cron.d/w2tj_scrapper_cron

RUN chmod 0644 /etc/cron.d/hw_scrapper_cron
RUN chmod 0644 /etc/cron.d/w2tj_scrapper_cron

RUN crontab /etc/cron.d/hw_scrapper_cron
RUN crontab /etc/cron.d/w2tj_scrapper_cron

RUN touch /var/log/cron.log

CMD cron && tail -f /var/log/cron.log
