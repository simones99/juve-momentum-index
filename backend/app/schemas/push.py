from pydantic import BaseModel


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    device_id: str | None = None
    locale: str = "it"
    notify_kickoff: bool = True
    notify_brief: bool = True
    notify_momentum: bool = True


class PushUnsubscribeIn(BaseModel):
    endpoint: str
