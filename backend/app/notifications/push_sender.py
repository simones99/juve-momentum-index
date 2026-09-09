"""Sends Web Push notifications to opted-in subscribers. Each of the three
event types (kickoff, brief, momentum) has its own opt-out flag on
PushSubscription, so a subscriber only gets what they asked for.

Silently a no-op when VAPID keys aren't configured, so subscribe/unsubscribe
still work in environments (e.g. CI, a fresh local checkout) that haven't
generated keys yet.
"""

import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

_NOTIFY_FLAG_BY_EVENT = {
    "kickoff": PushSubscription.notify_kickoff,
    "brief": PushSubscription.notify_brief,
    "momentum": PushSubscription.notify_momentum,
}


def notify_subscribers(db: Session, event: str, payload: dict) -> int:
    """Sends `payload` (JSON-encoded) to every subscription opted into
    `event` ("kickoff" | "brief" | "momentum"). Returns the number of
    successful sends. Subscriptions the push service reports as gone
    (404/410, e.g. the user uninstalled the browser or cleared site data)
    are deleted so they stop being retried."""
    settings = get_settings()
    if not settings.vapid_private_key:
        logger.info("push notifications disabled (no VAPID_PRIVATE_KEY configured); skipping %s", event)
        return 0

    flag = _NOTIFY_FLAG_BY_EVENT[event]
    subscriptions = list(db.scalars(select(PushSubscription).where(flag.is_(True))))

    data = json.dumps(payload)
    sent = 0
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=data,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
            sent += 1
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (404, 410):
                db.delete(sub)
            else:
                logger.warning("push send failed for subscription id=%s: %s", sub.id, exc)

    db.commit()
    return sent
