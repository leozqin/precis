FROM python:3.11-slim

WORKDIR /app
ENV IS_DOCKER=True

RUN apt-get -y update; apt-get -y install curl

COPY app ./app/
COPY assets ./assets/
COPY pyproject.toml .

RUN pip install .
RUN playwright install --with-deps chromium

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "80"]
HEALTHCHECK --interval=10s --timeout=10s --retries=5 CMD curl --include --request GET "http://localhost:80/health" || exit 1

EXPOSE 80
