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
        assert task["approval_required"] is False
        assert task["approval_status"] is None
        assert task["error"] is None

        task_id = task["id"]
        fetched = client.get(f"/api/v1/tasks/{task_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == task_id

        artifacts = client.get(f"/api/v1/tasks/{task_id}/artifacts")
        assert artifacts.status_code == 200
        assert artifacts.json() == []

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


def test_high_impact_task_waits_for_approval_then_runs() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/tasks",
            json={"goal": "Deploy to production after validating the release"},
        )
        assert created.status_code == 200
        task = created.json()
        assert task["status"] == "waiting_approval"
        assert task["approval_required"] is True
        assert task["approval_status"] == "pending"
        assert task["codex_thread_id"] is None

        waiting = client.get("/api/v1/tasks", params={"status": "waiting_approval"})
        assert waiting.status_code == 200
        waiting_tasks = waiting.json()
        assert task["id"] in {item["id"] for item in waiting_tasks}
        assert all(item["status"] == "waiting_approval" for item in waiting_tasks)

        approved = client.post(
            f"/api/v1/tasks/{task['id']}/approve",
            json={"note": "Release owner approved"},
        )
        assert approved.status_code == 200
        approved_task = approved.json()
        assert approved_task["status"] == "completed"
        assert approved_task["approval_status"] == "approved"
        assert approved_task["codex_thread_id"].startswith("stub:")

        events = client.get(f"/api/v1/tasks/{task['id']}/events").json()
        assert [event["event_type"] for event in events] == [
            "task.created",
            "approval.requested",
            "approval.approved",
            "task.started",
            "task.completed",
        ]


def test_high_impact_continuation_can_be_rejected() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/tasks",
            json={"goal": "Inspect release readiness"},
        ).json()

        gated = client.post(
            f"/api/v1/tasks/{created['id']}/continue",
            json={"instruction": "Publish publicly once checks pass"},
        )
        assert gated.status_code == 200
        gated_task = gated.json()
        assert gated_task["status"] == "waiting_approval"
        assert gated_task["approval_status"] == "pending"
        assert gated_task["pending_instruction"] == "Publish publicly once checks pass"

        rejected = client.post(
            f"/api/v1/tasks/{created['id']}/reject",
            json={"note": "Not ready for public release"},
        )
        assert rejected.status_code == 200
        rejected_task = rejected.json()
        assert rejected_task["status"] == "cancelled"
        assert rejected_task["approval_status"] == "rejected"
        assert rejected_task["pending_instruction"] is None
