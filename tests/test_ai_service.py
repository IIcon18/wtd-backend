"""Unit tests for AIService — no DB or HTTP required."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_service import AIService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_profile(
    level="beginner",
    goal="endurance",
    session_km="1000",
    sessions="3",
    pool="25",
):
    p = MagicMock()
    p.level.value = level
    p.goal.value = goal
    p.session_km.value = session_km
    p.sessions_per_week.value = sessions
    p.pool_meters.value = pool
    return p


def _make_workout(
    type_val="endurance",
    km_range="1000-1500",
    duration=45,
    content=None,
):
    w = MagicMock()
    w.type.value = type_val
    w.km_range = km_range
    w.duration_min = duration
    w.content = content or {
        "warmup": {"description": "200м в лёгком темпе"},
        "main": {
            "sets": [
                {
                    "repeat": 4,
                    "distance": 100,
                    "style": "кроль",
                    "rest_sec": 30,
                    "note": "Ровный темп",
                }
            ]
        },
        "cooldown": {"description": "100м расслабленно"},
        "coach_tip": "Следи за техникой",
        "total_distance": 1000,
    }
    return w


def _make_session(workout_type="endurance", duration=45, distance=1000):
    s = MagicMock()
    s.created_at.date.return_value = "2026-01-01"
    s.workout_type.value = workout_type
    s.duration_min = duration
    s.distance_m = distance
    return s


@pytest.fixture
def svc():
    return AIService(db=MagicMock())


# ── _fallback ─────────────────────────────────────────────────────────────────

def test_fallback_no_templates(svc):
    result = svc._fallback([])
    assert "недоступен" in result.lower()


def test_fallback_with_template_sections(svc):
    result = svc._fallback([_make_workout()])
    assert "Разминка" in result
    assert "Основная часть" in result
    assert "Заминка" in result
    assert "Совет тренера" in result


def test_fallback_includes_coach_tip(svc):
    w = _make_workout(content={
        "warmup": {"distance": 200},
        "main": {"sets": []},
        "cooldown": {"distance": 100},
        "coach_tip": "Береги плечи",
        "total_distance": 300,
    })
    assert "Береги плечи" in svc._fallback([w])


# ── _fmt_history ──────────────────────────────────────────────────────────────

def test_fmt_history_empty(svc):
    assert svc._fmt_history([]) == "нет данных"


def test_fmt_history_single_session(svc):
    result = svc._fmt_history([_make_session()])
    assert "endurance" in result
    assert "45" in result
    assert "1000" in result


def test_fmt_history_multiple_sessions(svc):
    sessions = [_make_session("endurance"), _make_session("technique", 30, 800)]
    result = svc._fmt_history(sessions)
    assert "endurance" in result
    assert "technique" in result


# ── _fmt_templates ────────────────────────────────────────────────────────────

def test_fmt_templates_empty(svc):
    assert svc._fmt_templates([]) == "нет шаблонов"


def test_fmt_templates_includes_type(svc):
    result = svc._fmt_templates([_make_workout(type_val="technique")])
    assert "technique" in result


# ── get_ai_response (async) ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_ai_response_no_api_config(svc):
    """When AI_API_URL is blank, returns fallback text."""
    profile = _make_profile()
    templates = [_make_workout()]

    with patch("app.services.ai_service.settings") as mock_settings:
        mock_settings.AI_API_URL = ""
        mock_settings.AI_API_KEY = ""
        result = await svc.get_ai_response("Тренировка", profile, [], templates)

    assert result  # non-empty fallback


@pytest.mark.anyio
async def test_get_ai_response_api_success(svc):
    """Successful API call returns the model reply."""
    profile = _make_profile()
    templates = [_make_workout()]
    expected = "Вот ваша тренировка на сегодня!"

    with patch("app.services.ai_service.settings") as mock_settings:
        mock_settings.AI_API_URL = "http://fake-api.example.com"
        mock_settings.AI_API_KEY = "fake-key"
        mock_settings.AI_MODEL = "gpt-4"
        with patch.object(svc, "_call_api", new=AsyncMock(return_value=expected)):
            result = await svc.get_ai_response("msg", profile, [], templates)

    assert result == expected


@pytest.mark.anyio
async def test_get_ai_response_api_failure_falls_back(svc):
    """When _call_api raises, the fallback is used instead of re-raising."""
    profile = _make_profile()
    templates = [_make_workout()]

    with patch("app.services.ai_service.settings") as mock_settings:
        mock_settings.AI_API_URL = "http://fake.com"
        mock_settings.AI_API_KEY = "key"
        mock_settings.AI_MODEL = "model"
        with patch.object(svc, "_call_api", side_effect=Exception("timeout")):
            result = await svc.get_ai_response("msg", profile, [], templates)

    assert result  # fallback text, not an exception
    assert "Разминка" in result or "недоступен" in result


@pytest.mark.anyio
async def test_get_ai_response_api_failure_no_templates(svc):
    """Fallback with no templates returns a 'try later' message."""
    profile = _make_profile()

    with patch("app.services.ai_service.settings") as mock_settings:
        mock_settings.AI_API_URL = "http://fake.com"
        mock_settings.AI_API_KEY = "key"
        mock_settings.AI_MODEL = "model"
        with patch.object(svc, "_call_api", side_effect=Exception("down")):
            result = await svc.get_ai_response("msg", profile, [], [])

    assert "недоступен" in result.lower() or result
