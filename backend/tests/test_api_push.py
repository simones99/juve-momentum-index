from app.models.push_subscription import PushSubscription


def _subscribe_body(endpoint: str = "https://push.example/1", **overrides) -> dict:
    body = {
        "endpoint": endpoint,
        "keys": {"p256dh": "p256dh-key", "auth": "auth-key"},
        "device_id": None,
        "locale": "it",
    }
    body.update(overrides)
    return body


def test_subscribe_creates_a_new_subscription(client, db):
    response = client.post("/api/v1/push/subscribe", json=_subscribe_body())

    assert response.status_code == 200
    saved = db.query(PushSubscription).filter_by(endpoint="https://push.example/1").first()
    assert saved is not None
    assert saved.p256dh == "p256dh-key"
    assert saved.notify_kickoff is True


def test_subscribe_upserts_on_repeat_endpoint(client, db):
    client.post("/api/v1/push/subscribe", json=_subscribe_body(locale="it"))
    client.post("/api/v1/push/subscribe", json=_subscribe_body(locale="en", notify_momentum=False))

    matches = db.query(PushSubscription).filter_by(endpoint="https://push.example/1").all()
    assert len(matches) == 1
    assert matches[0].locale == "en"
    assert matches[0].notify_momentum is False


def test_unsubscribe_deletes_the_subscription(client, db):
    client.post("/api/v1/push/subscribe", json=_subscribe_body())

    response = client.post("/api/v1/push/unsubscribe", json={"endpoint": "https://push.example/1"})

    assert response.status_code == 200
    assert db.query(PushSubscription).filter_by(endpoint="https://push.example/1").first() is None


def test_unsubscribe_unknown_endpoint_is_a_no_op(client):
    response = client.post("/api/v1/push/unsubscribe", json={"endpoint": "https://push.example/never-existed"})

    assert response.status_code == 200
