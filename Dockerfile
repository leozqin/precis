FROM nikolaik/python-nodejs:python3.11-nodejs22-slim

WORKDIR /app
ENV IS_DOCKER=True

RUN apt-get -y update; apt-get -y install curl
RUN pip install uv

COPY app ./app/
COPY pyproject.toml .
COPY tailwind.config.js .

RUN uv pip install --system .
RUN playwright install --with-deps chromium
RUN npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
RUN npx tailwindcss -i ./app/templates/input.css -o ./app/static/output.css --minify

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "80"]
HEALTHCHECK --interval=10s --timeout=10s --retries=5 CMD curl --include --request GET "http://localhost:80/health" || exit 1

EXPOSE 80
