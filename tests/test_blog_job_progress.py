from src.services import blog_job


def test_sections_prepared_is_emitted_after_every_worker_finishes(monkeypatch):
    events = []
    monkeypatch.setattr(blog_job, "update_job", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        blog_job,
        "save_job_event",
        lambda _thread_id, event_type, _event_data=None: events.append(
            event_type
        ),
    )
    monkeypatch.setattr(
        blog_job,
        "save_section_event",
        lambda _thread_id, _section: events.append("section_completed"),
    )

    expected_task_ids = {"1", "2"}
    completed_task_ids = set()
    sections_started_sent = False
    sections_prepared_sent = False

    sections_started_sent, sections_prepared_sent = (
        blog_job.record_worker_update(
            "thread",
            {"sections": [(1, "First section")]},
            expected_task_ids,
            completed_task_ids,
            sections_started_sent,
            sections_prepared_sent,
        )
    )

    assert "sections_started" in events
    assert "sections_prepared" not in events

    sections_started_sent, sections_prepared_sent = (
        blog_job.record_worker_update(
            "thread",
            {"sections": [(2, "Second section")]},
            expected_task_ids,
            completed_task_ids,
            sections_started_sent,
            sections_prepared_sent,
        )
    )

    assert sections_started_sent
    assert sections_prepared_sent
    assert events[-2:] == ["section_completed", "sections_prepared"]
