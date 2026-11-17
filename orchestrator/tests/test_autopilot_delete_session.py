"""Deleting an AutoPilot session must remove every row that references it."""

from __future__ import annotations

import asyncio

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from orchestrator.api.autopilot import delete_session
from orchestrator.api.models_db import (
    AutoPilotAgentAttempt,
    AutoPilotChecklistItem,
    AutoPilotPhase,
    AutoPilotSession,
)


def _engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _enforce_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")  # behave like PostgreSQL

    SQLModel.metadata.create_all(engine)
    return engine


def test_delete_session_removes_checklist_items_and_agent_attempts():
    engine = _engine()
    session_id = "autopilot_2026-11-17_17-50-39"
    with Session(engine) as db:
        db.add(AutoPilotSession(id=session_id, status="completed"))
        db.commit()
        db.add(AutoPilotPhase(session_id=session_id, phase_name="exploration", phase_order=0))
        db.add(AutoPilotChecklistItem(session_id=session_id, title="Explore the application"))
        db.add(AutoPilotAgentAttempt(session_id=session_id, stable_key="exploration:1"))
        db.commit()

    with Session(engine) as db:
        result = asyncio.run(delete_session(session_id, session=db))

    assert result == {"status": "deleted", "session_id": session_id}
    with Session(engine) as db:
        assert db.get(AutoPilotSession, session_id) is None
        for model in (AutoPilotPhase, AutoPilotChecklistItem, AutoPilotAgentAttempt):
            assert db.exec(select(model).where(model.session_id == session_id)).all() == []
