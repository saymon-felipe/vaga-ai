FROM python:3.11-bookworm

WORKDIR /app

# 1. Copia apenas o arquivo de requisitos primeiro
COPY requirements.txt .

# 2. Instala as bibliotecas do Python (AQUI o comando 'playwright' é criado)
RUN pip install --no-cache-dir -r requirements.txt

# 3. Baixa o navegador Chromium
RUN playwright install chromium

# 4. Instala as dependências do sistema operacional (com a proteção contra queda de rede)
RUN apt-get update && playwright install-deps || (sleep 5 && apt-get update && playwright install-deps)

# 5. Copia o restante do código do Worker
COPY . .

# 6. Inicia o Worker
CMD ["python", "main.py"]