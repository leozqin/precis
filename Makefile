.PHONY: tw
tw:
	npx tailwindcss -i ./app/templates/input.css -o ./app/static/output.css --watch --minify

.PHONY: install
install:
	npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
	pip install -e .
	playwright install --with-deps chromium

.PHONY: run
run:
	uvicorn app.app:app --reload --log-level debug

.PHONY: dev
dev:
	make install
	pre-commit install

.PHONY: build
build:
	docker compose -f docker-compose-dev.yml up --build
