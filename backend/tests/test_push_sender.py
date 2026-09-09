from types import SimpleNamespace

import app.notifications.push_sender as push_sender
from app.models.push_subscription import PushSubscription
from pywebpush import WebPushException


def _fake_settings(vapid_private_key: str = "priv", vapid_subject: str = "mailto:a@b.com") -> SimpleNamespace:
    return SimpleNamespace(vapid_private_key=vapid_private_key, vapid_subject=vapid_subject)


def _make_subscription(**overrides) -> PushSubscription:
    defaults = dict(
        endpoint="https://push.example/1",
        p256dh="p256dh-key",
        auth="auth-key",
        device_id=None,
        locale="it",
        notify_kickoff=True,
        notify_brief=True,
        notify_momentum=True,
    )
    defaults.update(overrides)
    return PushSubscription(**defaults)


def test_returns_zero_and_skips_send_when_vapid_not_configured(monkeypatch, db):
    monkeypatch.setattr(push_sender, "get_settings", lambda: _fake_settings(vapid_private_key=""))
    db.add(_make_subscription())
    db.commit()

    calls = []
    monkeypatch.setattr(push_sender, "webpush", lambda **kwargs: calls.append(kwargs))

    sent = push_sender.notify_subscribers(db, "kickoff", {"title": "Kickoff!"})

    assert sent == 0
    assert calls == []


def test_sends_only_to_subscribers_opted_into_the_event(monkeypatch, db):
    monkeypatch.setattr(push_sender, "get_settings", lambda: _fake_settings())
    db.add(_make_subscription(endpoint="https://push.example/in", notify_momentum=True))
    db.add(_make_subscription(endpoint="https://push.example/out", notify_momentum=False))
    db.commit()

    calls = []
    monkeypatch.setattr(push_sender, "webpush", lambda **kwargs: calls.append(kwargs))

    sent = push_sender.notify_subscribers(db, "momentum", {"title": "Momentum swing"})

    assert sent == 1
    assert calls[0]["subscription_info"]["endpoint"] == "https://push.example/in"


def test_expired_subscription_is_deleted_on_410(monkeypatch, db):
    monkeypatch.setattr(push_sender, "get_settings", lambda: _fake_settings())
    db.add(_make_subscription(endpoint="https://push.example/gone"))
    db.commit()

    def _raise(**kwargs):
        raise WebPushException("gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr(push_sender, "webpush", _raise)

    sent = push_sender.notify_subscribers(db, "brief", {"title": "Brief ready"})

    assert sent == 0
    remaining = db.query(PushSubscription).filter_by(endpoint="https://push.example/gone").first()
    assert remaining is None


def test_other_webpush_errors_are_logged_and_subscription_kept(monkeypatch, db):
    monkeypatch.setattr(push_sender, "get_settings", lambda: _fake_settings())
    db.add(_make_subscription(endpoint="https://push.example/flaky"))
    db.commit()

    def _raise(**kwargs):
        raise WebPushException("server error", response=SimpleNamespace(status_code=500))

    monkeypatch.setattr(push_sender, "webpush", _raise)

    sent = push_sender.notify_subscribers(db, "brief", {"title": "Brief ready"})

    assert sent == 0
    remaining = db.query(PushSubscription).filter_by(endpoint="https://push.example/flaky").first()
    assert remaining is not None
