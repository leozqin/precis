![The Precis logo... for now](assets/logo-with-name-light.svg)
--
Precis (properly Précis, pronounced "pray-see") is a extensibility-oriented RSS reader that can use LLMs to summarize and synthesize information from numerous different sources, with an emphasis on timely delivery of information via notifications.

The following components of the app are extensible:
1. Summarization - LLMs including Ollama and OpenAI
2. Content Retrieval - `requests` or `playwright`
3. Notification - `matrix` or `slack`, but support for other protocols such as `discord` or `mattermost`, or push-based services such as `gotify` or `ntfy`, or even a message bus such as `kafka`.
4. Storage - `tinydb`

## Architecture
Precis is a FastAPI monolith that serves fully static pages styled by Tailwind CSS using DaisyUI components.

## Deployment via Docker-Compose:
If you want to run via docker-compose:
```bash
docker compose up
```

## Pre-Requisites
- Python 3.12 or higher (use pyenv)
- Node 20 or higher (use nvm)

## Development Instructions
To install, create a fresh venv and then:
```bash
make dev
```
Then to develop, in one terminal start tailwind by doing `make tw`. Then, in other start the main app by doing `make run`.
