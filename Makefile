.PHONY: tw
tw:
	npx tailwindcss -i ./app/templates/input.css -o ./app/static/output.css --watch --minify

.PHONY: install
install:
	npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
	pip install -e .
	playright install --with-deps chromium

.PHONY: run
run:
	uvicorn app.app:app --reload

.PHONY: dev
dev:
	make install
	pre-commit install
