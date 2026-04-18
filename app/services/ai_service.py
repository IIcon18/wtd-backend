import logging
from typing import List

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.swim_profile import SwimProfile
from app.models.user_session import UserSession
from app.models.workout import Workout

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """
Ты персональный тренер по плаванию. Отвечай по-русски.

Профиль: уровень={level}, цель={goal},
километраж={session_km}м, частота={sessions_per_week}/нед,
бассейн={pool_meters}м

Последние тренировки: {history}
Шаблоны из БД: {templates}

Правила:
- Не повторяй тип тренировки два дня подряд
- Если пользователь устал — предлагай recovery
- Формат: разминка / основная часть / заминка / совет тренера
- Если вопрос не про тренировку — отвечай как тренер-консультант
"""


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ai_response(
        self,
        user_message: str,
        profile: SwimProfile,
        history: List[UserSession],
        templates: List[Workout],
    ) -> str:
        system_prompt = _SYSTEM_PROMPT.format(
            level=profile.level.value,
            goal=profile.goal.value,
            session_km=profile.session_km.value,
            sessions_per_week=profile.sessions_per_week.value,
            pool_meters=profile.pool_meters.value,
            history=self._fmt_history(history),
            templates=self._fmt_templates(templates),
        )

        if settings.AI_API_URL and settings.AI_API_KEY:
            try:
                return await self._call_api(system_prompt, user_message)
            except Exception as exc:
                logger.warning("AI API недоступен (%s), используем fallback", exc)

        return self._fallback(templates)

    async def _call_api(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.AI_API_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _fmt_history(self, history: List[UserSession]) -> str:
        if not history:
            return "нет данных"
        return "; ".join(
            f"{s.created_at.date()} — {s.workout_type.value}, "
            f"{s.duration_min} мин, {s.distance_m} м"
            for s in history
        )

    def _fmt_templates(self, templates: List[Workout]) -> str:
        if not templates:
            return "нет шаблонов"
        return "; ".join(
            f"{w.type.value} {w.km_range}м ({w.duration_min} мин): "
            f"{w.content.get('coach_tip', '')}"
            for w in templates
        )

    def _fallback(self, templates: List[Workout]) -> str:
        if not templates:
            return "AI-тренер временно недоступен. Попробуйте позже."

        w = templates[0]
        c = w.content
        wu = c.get("warmup", {})
        main = c.get("main", {})
        cd = c.get("cooldown", {})
        tip = c.get("coach_tip", "Хорошей тренировки!")

        sets_lines = ""
        for s in main.get("sets", []):
            sets_lines += (
                f"  {s.get('repeat', '')}×{s.get('distance', '')}м "
                f"{s.get('style', '')} "
                f"(отдых {s.get('rest_sec', '')}с) — {s.get('note', '')}\n"
            )

        warmup_text = wu.get("description") or f"{wu.get('distance', '')}м"
        cooldown_text = cd.get("description") or f"{cd.get('distance', '')}м"
        return (
            f"**Разминка:** {warmup_text}\n\n"
            f"**Основная часть:**\n{sets_lines}\n"
            f"**Заминка:** {cooldown_text}\n\n"
            f"**Совет тренера:** {tip}"
        )