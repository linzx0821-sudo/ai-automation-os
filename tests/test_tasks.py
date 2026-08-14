from fastapi.testclient import TestClient

from app.main import app


def test_task_create_get_continue_and_events() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/tasks",
            json={"goal": "Inspect this workspace and report readiness"},
        )
        assert created.status_code == 200
        task = created.json()
        assert task["status"] == "completed"
        assert task["codex_thread_id"].startswith("stub:")
        assert task["error"] is None

        task_id = task["id"]
        fetched = client.get(f"/api/v1/tasks/{task_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == task_id

        continued = client.post(
            f"/api/v1/tasks/{task_id}/continue",
            json={"instruction": "Continue with the next safe step"},
        )
        assert continued.status_code == 200
        assert continued.json()["codex_thread_id"] == task["codex_thread_id"]
        assert continued.json()["status"] == "completed"

        events = client.get(f"/api/v1/tasks/{task_id}/events")
        assert events.status_code == 200
        event_types = [event["event_type"] for event in events.json()]
        assert event_types == [
            "task.created",
            "task.started",
            "task.completed",
            "task.resumed",
            "task.completed",
        ]
