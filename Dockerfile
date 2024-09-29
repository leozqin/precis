FROM node:22-slim as tw

WORKDIR /app
COPY app ./app/
COPY tailwind.config.js .
RUN npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
RUN npx tailwindcss -i ./app/templates/input.css -o ./output.css --minify

FROM python:3.11-slim as py
RUN pip install uv
WORKDIR /app
COPY pyproject.toml .
RUN uv venv
RUN uv pip install .

FROM nikolaik/python-nodejs:python3.11-nodejs22-slim as web

LABEL org.opencontainers.image.title="Precis"
LABEL org.opencontainers.image.authors="leozqin@gmail.com"
LABEL org.opencontainers.image.source="https://github.com/leozqin/precis"
LABEL org.opencontainers.image.url="https://github.com/leozqin/precis"
LABEL org.opencontainers.image.description="An extensible self-hosted AI-enabled RSS reader with a focus on notifications and support for theming"
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /app
ENV IS_DOCKER=True

COPY app ./app/

COPY --from=py /app/.venv /app/.venv
COPY --from=tw /app/output.css /app/app/static/output.css
ENV PATH /app/.venv/bin:$PATH
RUN playwright install --with-deps chromium


CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "80"]
HEALTHCHECK --interval=10s --timeout=10s --retries=5 CMD curl --include --request GET "http://localhost:80/health" || exit 1

EXPOSE 80
