from uuid import uuid4
from typing import Any
import os

_sessions: dict[str, dict[str, Any]] = {}


def create_session(assessment: dict, prediction: dict) -> str:
    session_id = str(uuid4())

    _sessions[session_id] = {
        "assessment": assessment,
        "prediction": prediction,
        "messages": [],
    }
    return session_id


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def add_user_message(session_id: str, message: str) -> None:
    session = get_session(session_id)

    if session is None:
        raise ValueError("Session not found.")

    session["messages"].append({
        "role": "user",
        "content": message
    })


def add_assistant_message(session_id: str, message: str) -> None:
    session = get_session(session_id)

    if session is None:
        raise ValueError("Session not found.")

    session["messages"].append({
        "role": "assistant",
        "content": message
    })


def get_messages(session_id: str) -> list[dict]:
    session = get_session(session_id)

    if session is None:
        raise ValueError("Session not found.")

    return session["messages"]
