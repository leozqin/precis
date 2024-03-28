FROM python:3.12-slim

WORKDIR /app

COPY rssynthesis ./rssynthesis/
COPY pyproject.toml .

RUN pip install .

CMD ["uvicorn", "rssynthesis.rssynthesis:app", "--host", "0.0.0.0", "--port", "80"]
EXPOSE 80