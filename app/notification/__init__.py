from enum import Enum

from app.notification.matrix import MatrixNotificationHandler
from app.notification.null import NullNotificationHandler
from app.notification.slack import SlackNotificationHandler

notification_handlers = {
    "matrix": MatrixNotificationHandler,
    "null_notification": NullNotificationHandler,
    "slack": SlackNotificationHandler,
}
