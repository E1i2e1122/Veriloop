"""k6 --summary-export thresholds are read correctly in both the old and the current format."""

from __future__ import annotations

import json

from orchestrator.utils.k6_result_parser import parse_summary


def _summary(tmp_path, thresholds_failed_rate, thresholds_duration):
    path = tmp_path / "summary.json"
    path.write_text(
        json.dumps(
            {
                "metrics": {
                    "http_req_failed": {"type": "rate", "values": {"rate": 0}, "thresholds": thresholds_failed_rate},
                    "http_req_duration": {"type": "trend", "values": {"p(95)": 106.0}, "thresholds": thresholds_duration},
                    "http_reqs": {"type": "counter", "values": {"count": 492, "rate": 7.2}},
                }
            }
        )
    )
    return parse_summary(str(path))


def test_current_format_with_passing_thresholds(tmp_path):
    summary = _summary(tmp_path, {"rate<0.01": {"ok": True}}, {"p(95)<800": {"ok": True}})

    assert summary["thresholds_passed"] is True
    assert summary["thresholds"] == {"http_req_failed{rate<0.01}": {"ok": True}, "http_req_duration{p(95)<800}": {"ok": True}}


def test_current_format_with_a_failed_threshold(tmp_path):
    summary = _summary(tmp_path, {"rate<0.01": {"ok": True}}, {"p(95)<100": {"ok": False}})

    assert summary["thresholds_passed"] is False
    assert summary["thresholds"]["http_req_duration{p(95)<100}"] == {"ok": False}


def test_legacy_format_where_true_means_crossed(tmp_path):
    summary = _summary(tmp_path, {"rate<0.01": False}, {"p(95)<100": True})

    assert summary["thresholds"] == {"http_req_failed{rate<0.01}": {"ok": True}, "http_req_duration{p(95)<100}": {"ok": False}}
    assert summary["thresholds_passed"] is False
