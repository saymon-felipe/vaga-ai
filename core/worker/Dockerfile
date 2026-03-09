FROM python:3.11-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y ca-certificates

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

RUN apt-get update && playwright install-deps

COPY . .

CMD ["python", "main.py"]