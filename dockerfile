FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y cron

# Rendre les scripts exécutables
RUN chmod +x /app/src/HW_Scrapper.py
RUN chmod +x /app/src/W2TJ_Scrapper.py

# Utiliser le chemin absolu du binaire Python et exécuter les scripts à 00h15
RUN echo "15 0 * * * $(which python) /app/src/HW_Scrapper.py >> /var/log/HW_Scrapper.log 2>&1" >> /etc/cron.d/scrapper_cron
RUN echo "15 0 * * * $(which python) /app/src/W2TJ_Scrapper.py >> /var/log/W2TJ_Scrapper.log 2>&1" >> /etc/cron.d/scrapper_cron

RUN chmod 0644 /etc/cron.d/scrapper_cron

# Charger les tâches cron dans la crontab
RUN crontab /etc/cron.d/scrapper_cron
RUN touch /var/log/cron.log /var/log/HW_Scrapper.log /var/log/W2TJ_Scrapper.log

# Démarrer le service cron et suivre les logs
CMD cron && tail -f /var/log/cron.log /var/log/HW_Scrapper.log /var/log/W2TJ_Scrapper.log
