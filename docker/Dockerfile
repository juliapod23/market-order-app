# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY configs /app/configs

ENV PYTHONPATH=/app/src
EXPOSE 8501

CMD ["streamlit", "run", "src/obp/ui_app.py", "--", "--config", "configs/default.yaml"]
