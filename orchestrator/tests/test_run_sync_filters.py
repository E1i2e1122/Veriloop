"""The startup run sync must only import real test-run folders from runs/."""

from orchestrator.api.test_run_read_model_support import is_test_run_dir


def test_infrastructure_folders_are_not_test_runs(tmp_path):
    for name in ("explorations", "appium-screenshots", "autonomous_validation"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "nested").mkdir()
        assert not is_test_run_dir(folder), name


def test_folders_with_run_artifacts_are_test_runs(tmp_path):
    for marker in ("plan.json", "run.json", "status.txt", "execution.log", "validation.json", "spec.md"):
        folder = tmp_path / f"2026-11-16_10-00-00-{marker.replace('.', '-')}"
        folder.mkdir()
        (folder / marker).write_text("{}")
        assert is_test_run_dir(folder), marker


def test_files_are_not_test_runs(tmp_path):
    stray = tmp_path / "notes.txt"
    stray.write_text("not a run")
    assert not is_test_run_dir(stray)
