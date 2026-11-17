"""Approved database suggestions must keep their names, types and severities when the spec is run."""

from __future__ import annotations

from orchestrator.api.database_testing import _checks_to_markdown
from orchestrator.workflows.db_spec_parser import _extract_sql_checks


def test_approved_suggestions_round_trip_through_the_spec_parser():
    suggestions = [
        {
            "check_name": "orders_no_null_customer",
            "check_type": "null_check",
            "severity": "high",
            "description": "Every order is linked to a customer.",
            "sql_query": "SELECT id FROM orders WHERE customer_id IS NULL LIMIT 100",
        },
        {
            "check_name": "orders_total_matches_line_items",
            "check_type": "custom",
            "severity": "critical",
            "sql_query": "SELECT o.id FROM orders o JOIN order_items i ON i.order_id = o.id GROUP BY o.id, o.total "
            "HAVING o.total <> SUM(i.quantity * i.unit_price) LIMIT 100",
        },
    ]

    checks = _extract_sql_checks(_checks_to_markdown("ai-suggested-checks.md", suggestions))

    assert [(c["check_name"], c["check_type"], c["severity"]) for c in checks] == [
        ("orders_no_null_customer", "null_check", "high"),
        ("orders_total_matches_line_items", "custom", "critical"),
    ]
    assert all(c["sql_query"].splitlines()[-1].startswith("SELECT") for c in checks)


def test_separator_characters_in_names_do_not_break_the_metadata_line():
    markdown = _checks_to_markdown("x.md", [{"check_name": "a|b", "check_type": "custom", "severity": "low", "sql_query": "SELECT 1"}])

    assert _extract_sql_checks(markdown)[0]["check_name"] == "a/b"
