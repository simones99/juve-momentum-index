from datetime import datetime, timezone

from app.models.ingest_run import IngestRun


def test_healthz_reports_null_when_no_ingest_ever_ran(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "last_successful_ingest_at": None}


def test_healthz_reports_the_latest_successful_ingest_timestamp(client, db):
    finished = datetime(2026, 9, 9, 3, 12, tzinfo=timezone.utc)
    db.add(
        IngestRun(
            started_at=finished,
            finished_at=finished,
            status="success",
            matches_upserted=42,
            source_summary="football-data:42",
        )
    )
    db.commit()

    response = client.get("/healthz")

    assert response.json() == {"status": "ok", "last_successful_ingest_at": finished.isoformat()}
