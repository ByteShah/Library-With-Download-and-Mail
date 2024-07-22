FROM python:3.12.4-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

COPY .env .env

EXPOSE 5000

CMD ["python", "run.py"]
