FROM python:3.11-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

RUN apt-get update && playwright install-deps || (sleep 5 && apt-get update && playwright install-deps)

COPY . .

CMD ["python", "main.py"]