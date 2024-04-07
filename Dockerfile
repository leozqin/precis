FROM python:3.12-slim

WORKDIR /app

COPY app ./app/
COPY pyproject.toml .

RUN pip install .
RUN playwright install --with-deps chromium

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "80"]
EXPOSE 80
