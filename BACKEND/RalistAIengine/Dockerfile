FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy requirements first for caching
COPY AiEngine/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy AI engine code
COPY AiEngine/ .

EXPOSE 8000

CMD ["python", "main.py"]
