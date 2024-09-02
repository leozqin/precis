from enum import Enum

from app.notification.jira import JiraNotificationHandler
from app.notification.matrix import MatrixNotificationHandler
from app.notification.ntfy import NtfyNotificationHandler
from app.notification.null import NullNotificationHandler
from app.notification.slack import SlackNotificationHandler

notification_handlers = {
    "matrix": MatrixNotificationHandler,
    "null_notification": NullNotificationHandler,
    "slack": SlackNotificationHandler,
    "jira": JiraNotificationHandler,
    "ntfy": NtfyNotificationHandler,
}
