![The Precis logo... for now](assets/logo-with-name-light.svg)
--
Precis (properly Précis, pronounced "pray-see") is a extensibility-oriented RSS reader that can use LLMs to summarize and synthesize information from numerous different sources, with an emphasis on timely delivery of information via notifications.

The following components of the app are extensible:
1. Summarization - LLMs including Ollama and OpenAI
2. Content Retrieval - `requests` or `playwright`
3. Notification - currently - `matrix` or `slack`, but support for other protocols such as `discord` or `mattermost`, or push-based services such as `gotify` or `ntfy`, or even a message bus such as `kafka`.
4. Storage - At this time, we support two reasonable embedded DBs - `tinydb` or `lmdb` - defaults to `tinydb`. You can add support for your database of choice if you can implement about 20 shared transactions.

The Summarization and Notification handlers also support a `null` handler that does nothing. Good for testing or if you don't care about notifications and summaries. The null handler is the default.

Precis also supports themes.

For an extended overview of why this project exists, see [my blog](https://www.leozqin.me/posts/precis-an-ai-enabled-rss-reader/)

## Architecture
Precis is a FastAPI monolith that serves fully static pages styled by Tailwind CSS using DaisyUI components. It uses some query-parameter and redirect chicanery to fake interactivity. We'll probably add actual interactivity at some point.

## Deployment via Docker-Compose:
If you want to run via docker-compose:
```bash
docker compose up
```
Feel free to edit the [docker-compose.yml](docker-compose.yml) as needed to fit your environment.

## Pre-Requisites
- Python 3.11 (for dev, we recommend you use pyenv)
- Node 20 or higher (use nvm)

## Development Instructions
To install, create a fresh venv and then:
```bash
make dev
```
Then to develop, in one terminal start tailwind by doing `make tw`. Then, in other start the main app by doing `make run`.

## OPML Import/Export
Precis supports exporting your current set of feeds as OPML, as well as importing feeds from other OPML files. You can find options on the `/feeds/` page, or use the CLI as described below.

A couple caveats:
1. When importing an OPML file, if the feed already exists then it will be upserted. Any properties that differ from the OPML file will change to match.
2. When importing an OPML file, Precis will take the first category as the category of the feed. You may always change the category at a later time.
3. When importing and exporting, we the map the feed name, feed url, and category to the outline item `text`, `xml_url`, and `categories[0]` attributes, respectively. Please ensure that your input file uses the same conventions.

## Backups
Precis supports exporting and importing point-in-time backups of the entire application state. You can find these options on the `/about/` page, or use the CLI as described below. One of the design goals of this functionality is supporting the ability to combine two different Precis instances, so the default behavior of the import functionality is to upsert.

Users should be careful about potentially importing the same backup twice, and importing backups that have overlapping content may cause unexpected behavior.

Finally - the backups will contain any API keys or other secrets that you've configured Precis to use, so they should themselves be treated as secrets.

## CLI
Precis includes a CLI tool that can be used to manage the application. Currently, it supports exporting and importing JSON backups and OPML files.

```bash
❯ precis --help
Usage: precis [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  backup       Write a json-format backup of the current Precis state to...
  export-opml  Write a opml-format list of the feeds configured in Precis...
  import-opml  Import an opml-formatted feed list into Precis
  restore      Restore a json-format backup of the Precis state
```

## UI Tour
After initial onboarding, you'll be brought to the feeds page.
![The feeds page](assets/feeds.png)

You can then view the feed entries for each feed.
![The feed entries page](assets/feed_entries.png)

When you read a feed entry you'll get the full text of the article, as well a summary if you have a summarization handler configured.
![The read page](assets/read.png)

Global settings can be configured in the UI
![The settings page](assets/settings.png)

Configuring individual handlers is as simple as following an JSON Schema spec. (At some point we'll make a real UI)
![The handler config page](assets/handler_config.png)
