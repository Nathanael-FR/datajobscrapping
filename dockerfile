FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y cron

RUN touch /var/log/cron.log

RUN (crontab -l ; echo "0 16 * * * /usr/local/bin/python /app/src/HW_Scrapper.py >> /var/log/cron.log 2>&1") | crontab
RUN (crontab -l ; echo "0 16 * * * /usr/local/bin/python /app/src/W2TJ_Scrapper.py >> /var/log/cron.log 2>&1") | crontab

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log


