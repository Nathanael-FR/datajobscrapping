FROM python:3.10.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./app

CMD [ "python", "./app.py" ]
