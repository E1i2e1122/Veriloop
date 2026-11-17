"""Progress callbacks must authenticate when the backend enforces auth."""

from __future__ import annotations

from types import SimpleNamespace

from orchestrator.utils import progress_reporter
from orchestrator.utils.progress_reporter import ProgressReporter


def _capture_posts(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(progress_reporter.requests, "post", fake_post)
    return calls


def test_callbacks_send_the_internal_token(monkeypatch):
    monkeypatch.setenv("VERILOOP_INTERNAL_TOKEN", "s3cret")
    calls = _capture_posts(monkeypatch)
    reporter = ProgressReporter("run-1", api_url="http://backend:8001")

    assert reporter.report("planning", "Exploring application structure...")
    assert reporter.report_agentic_summary({"status": "passed"})

    assert [url for url, _ in calls] == [
        "http://backend:8001/runs/run-1/progress",
        "http://backend:8001/runs/run-1/agentic-summary",
    ]
    for _, kwargs in calls:
        assert kwargs["headers"] == {"X-Veriloop-Internal-Token": "s3cret"}


def test_callbacks_send_no_token_header_when_none_is_configured(monkeypatch):
    monkeypatch.delenv("VERILOOP_INTERNAL_TOKEN", raising=False)
    calls = _capture_posts(monkeypatch)

    ProgressReporter("run-1", api_url="http://backend:8001").report("testing")

    assert calls[0][1]["headers"] == {}
