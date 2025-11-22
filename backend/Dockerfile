FROM python:3.12-slim

# Não criar .pyc e sempre logar direto no stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema (psycopg2, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# O código será montado via volume em dev,
# mas copiamos também pra facilitar build em prod depois
COPY . .

# Em prod vamos rodar o gunicorn. Em dev o docker-compose vai sobrescrever esse comando.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
