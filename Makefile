.PHONY: tw
tw:
	npx tailwindcss -i ./app/templates/input.css -o ./app/static/output.css --watch --minify

.PHONY: install
install:
	npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
	pip install -e .
	playwright install --with-deps chromium

.PHONY: install-ci
install-ci:
	npm install -D tailwindcss @tailwindcss/typography daisyui@latest @tailwindcss/forms
	uv pip install .
	playwright install --with-deps chromium

.PHONY: run
run:
	uvicorn app.app:app --reload --log-level debug

.PHONY: run-ci
run-ci:
	uvicorn app.app:app &

.PHONY: dev
dev:
	make install
	pre-commit install

.PHONY: build
build:
	docker compose up --build

.PHONY: clean
clean:
	rm *.mdb db.json

.PHONY: test
test:
	go test tests/integration/*.go -v
