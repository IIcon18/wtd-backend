import logging
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.swim_profile import SwimProfile
from app.models.user_session import UserSession
from app.models.workout import Workout

logger = logging.getLogger(__name__)

_GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
_GIGACHAT_CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

_SYSTEM_PROMPT = """
Ты персональный тренер по плаванию. Отвечай по-русски.

Профиль пловца:
- Уровень: {level}
- Цель: {goal}
- Объём тренировки: {session_km}м
- Частота: {sessions_per_week} раз в неделю
- Бассейн: {pool_meters}м

Последние тренировки: {history}
Шаблоны из БД: {templates}

---

Правила составления тренировки:
- Не повторяй тип тренировки два дня подряд
- Если пользователь устал или просит лёгкую — предлагай recovery
- Объём разминки: ~15–20% от общего, заминки: ~10%
- Указывай инвентарь прямо в упражнении: (доска), (ласты), (лопатки), (трубка)
- Для серий с нумерацией — описывай каждый отрезок с новой строки и цифрой
- Отдых пиши в скобках в конце строки: (отдых 30с)
- В конце всегда пиши итоговый метраж: Итог: XХХХм

---

Строго используй этот формат вывода:

Разминка
[упражнения]

Основное
[упражнения]

Заминка
[упражнения]

Итог: [метраж]м

💬 Совет тренера: [короткий практический совет по технике или восстановлению]

---

Правила форматирования текста:
- Заголовки разделов — без решёток и звёздочек, просто слово с новой строки
- Серии пиши как: 4х100, 8 по 50, 4 бассейна
- Если серия с вариациями — нумеруй каждый повтор:
  1. Правый бок
  2. Левый бок
  3. На животе руки в стрелочки
  4. На спине руки в стрелочки
- Пиши компактно и без лишних слов — как тренер на бортике, а не как учебник
- Не используй markdown-разметку (жирный, курсив, списки с дефисами)

---

Если вопрос не про тренировку — отвечай как опытный тренер-консультант:
кратко, по делу, с практическим советом.
"""


@dataclass
class _TokenCache:
    token: str
    expires_at: float  # unix timestamp (seconds)


_token_cache: Optional[_TokenCache] = None


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

        if settings.GIGACHAT_CREDENTIALS:
            try:
                return await self._call_gigachat(system_prompt, user_message)
            except Exception as exc:
                logger.warning("GigaChat недоступен (%s), пробуем резервный API", exc)

        if settings.AI_API_URL and settings.AI_API_KEY:
            try:
                return await self._call_api(system_prompt, user_message)
            except Exception as exc:
                logger.warning("AI API недоступен (%s), используем fallback", exc)

        return self._fallback(templates)

    # ------------------------------------------------------------------ GigaChat

    async def _get_gigachat_token(self) -> str:
        global _token_cache
        if _token_cache and _token_cache.expires_at > time.time() + 60:
            return _token_cache.token

        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            resp = await client.post(
                _GIGACHAT_AUTH_URL,
                headers={
                    "Authorization": f"Basic {settings.GIGACHAT_CREDENTIALS}",
                    "RqUID": str(uuid.uuid4()),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": settings.GIGACHAT_SCOPE},
            )
            resp.raise_for_status()
            data = resp.json()

        _token_cache = _TokenCache(
            token=data["access_token"],
            expires_at=data["expires_at"] / 1000,  # мс → секунды
        )
        return _token_cache.token

    async def _call_gigachat(self, system_prompt: str, user_message: str) -> str:
        token = await self._get_gigachat_token()
        payload = {
            "model": settings.GIGACHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            resp = await client.post(
                _GIGACHAT_CHAT_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    # ------------------------------------------------------------------ Generic OpenAI-compatible API

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

    # ------------------------------------------------------------------ helpers

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
