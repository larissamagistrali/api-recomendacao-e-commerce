FROM python:3.12-slim

# Diretório de trabalho
WORKDIR /app

# Copia o código
COPY ./api /app/api
COPY ./api/requirements.txt /app/requirements.txt

# Instala dependências
RUN pip install --no-cache-dir -r /app/requirements.txt

# Define o PYTHONPATH para que "import api" funcione
ENV PYTHONPATH=/app

# Expõe a porta da API
EXPOSE 8000

# Comando padrão
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
