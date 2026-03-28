FROM python:3.11-slim

WORKDIR /app

# Copy requirements from AiEngine folder
COPY AiEngine/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the AI engine code
COPY AiEngine/ .

EXPOSE 8000
CMD ["python", "main.py"]