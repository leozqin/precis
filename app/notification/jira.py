from logging import getLogger
from os import environ
from re import sub
from typing import ClassVar, Mapping

from jira import JIRA

from app.handlers import NotificationHandler
from app.models import Feed, FeedEntry

logger = getLogger("uvicorn.error")


class JiraNotificationHandler(NotificationHandler):
    id: ClassVar[str] = "jira"
    token: str = environ.get("JIRA_API_TOKEN")
    email: str = environ.get("JIRA_EMAIL")
    server: str
    project: str
    routing: Mapping[str, str] = {}

    @staticmethod
    def labelfy(label: str) -> str:
        return "-".join(
            sub(
                r"(\s|_|-)+",
                " ",
                sub(
                    r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                    lambda mo: " " + mo.group(0).lower(),
                    label,
                ),
            ).split()
        )

    async def send_notification(self, feed: Feed, entry: FeedEntry):
        server = JIRA(server=self.server, basic_auth=(self.email, self.token))
        server._options.update({"rest_api_version": 3})

        summary = f"{feed.name}: {entry.title}"

        if feed.notify_destination:
            project = self.routing.get(feed.notify_destination, self.project)
            logger.info(
                "Creating issue in project " f"{feed.notify_destination} - {project}"
            )
        else:
            project = self.project
            logger.info(f"Sending notification to default channel {project}")

        description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "text": entry.preview,
                            "type": "text",
                        }
                    ],
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Read in Precis",
                                            "marks": [
                                                {
                                                    "type": "link",
                                                    "attrs": {
                                                        "href": self.make_read_link(
                                                            entry
                                                        ),
                                                    },
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "Read Original",
                                            "marks": [
                                                {
                                                    "type": "link",
                                                    "attrs": {
                                                        "href": entry.url,
                                                    },
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ],
                        },
                    ],
                },
            ],
        }

        server.create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": "Task"},
            labels=[self.labelfy(feed.name), self.labelfy(feed.category)],
        )
