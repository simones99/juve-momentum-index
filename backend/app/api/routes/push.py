from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.push_subscription import PushSubscription
from app.schemas.push import PushSubscriptionIn, PushUnsubscribeIn

router = APIRouter(tags=["push"])


@router.post("/push/subscribe")
def subscribe(body: PushSubscriptionIn, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    if existing is None:
        existing = PushSubscription(endpoint=body.endpoint)
        db.add(existing)

    existing.p256dh = body.keys.p256dh
    existing.auth = body.keys.auth
    existing.device_id = body.device_id
    existing.locale = body.locale
    existing.notify_kickoff = body.notify_kickoff
    existing.notify_brief = body.notify_brief
    existing.notify_momentum = body.notify_momentum

    db.commit()
    return {"status": "ok"}


@router.post("/push/unsubscribe")
def unsubscribe(body: PushUnsubscribeIn, db: Session = Depends(get_db)) -> dict:
    db.execute(delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    db.commit()
    return {"status": "ok"}
