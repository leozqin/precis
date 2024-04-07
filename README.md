# Precis
Precis (properly Précis, pronounced "pray-see") is a extensibility-oriented RSS reader that can use LLMs to summarize and synthesize information from numerous different sources, with an emphasis on timely delivery of information via notifications.

The following components of the app are extensible:
1. Summarization - LLMs including Ollama (soon: OpenAI and/or a generic Langchain implementation)
2. Content Retrieval - `requests` or `playwright`
3. Notification - `matrix` is currently only supported, but it should be possible to implement support for other messaging protocols like `slack` or `mattermost`, push-based services such as `gotify` or `ntfy`, or even a message bus such as `kafka`.
4. Storage - `tinydb` (soon: `MySQL` - a vector DB storage backend could **very** interesting, though)

## Architecture
Precis is a FastAPI monolith that serves fully static pages styled by Tailwind CSS using DaisyUI components.

## Pre-Requisites
- Python 3.11 or higher (use pyenv)
- Node 20 or higher (use nvm)

## Development Instructions
To install, create a fresh venv and then:
```bash
make dev
```
Then to develop, in one terminal start tailwind by doing `make tw`. Then, in other start the main app by doing `make run`.

## To run locally:
If you want to run via docker-compose:
```bash
docker compose up
```
