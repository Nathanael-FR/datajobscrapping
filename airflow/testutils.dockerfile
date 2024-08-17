FROM python:3.10-slim-buster

COPY requirements.txt /app/requirements.txt
COPY /utils /app

WORKDIR /app

RUN pip install -r requirements.txt 

# Keep the container running
CMD tail -f /dev/null

