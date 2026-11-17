"""Run coverage only counts specs in scope, so it never goes above 100%."""

from __future__ import annotations

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from orchestrator.api import analytics, projects
from orchestrator.api.models_db import SpecMetadata, TestRun


def test_runs_of_specs_outside_the_project_do_not_count(tmp_path, monkeypatch):
    specs_dir = tmp_path / "specs"
    (specs_dir / "shop").mkdir(parents=True)
    for name in ("search.md", "login.md"):
        (specs_dir / "shop" / name).write_text("# spec\n")
    monkeypatch.setattr(projects, "SPECS_DIR", specs_dir)
    monkeypatch.setattr(analytics, "SPECS_DIR", specs_dir)
    monkeypatch.setattr(analytics, "TESTS_DIR", tmp_path / "tests" / "generated")

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        for name in ("shop/search.md", "shop/login.md"):
            db.add(SpecMetadata(spec_name=name, project_id="shop", tags_json="[]"))
        db.add(TestRun(id="run-1", spec_name="shop/search.md", status="passed", project_id="shop"))
        db.add(TestRun(id="run-2", spec_name="shop/search.md", status="failed", project_id="shop"))
        # An API-test run and a run of a spec that no longer exists, both in the same project.
        db.add(TestRun(id="run-3", spec_name="openapi-operations.md", status="failed", project_id="shop"))
        db.add(TestRun(id="run-4", spec_name="shop/deleted.md", status="passed", project_id="shop"))
        db.commit()

        overview = analytics.get_coverage_overview(project_id="shop", session=db)

    assert overview["total_specs"] == 2
    assert overview["specs_run_at_least_once"] == 1
    assert overview["run_coverage_percent"] == 50.0
