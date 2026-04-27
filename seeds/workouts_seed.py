"""
Seed: 30 workout templates (10 beginner, 10 intermediate, 10 advanced).
Run: docker compose exec app python seeds/workouts_seed.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.workout import Workout

WORKOUTS = [
    # ── BEGINNER ─────────────────────────────────────────────────────────────
    {
        "level": "beginner", "type": "technique", "duration_min": 30,
        "pool_meters": 25, "km_range": "1000",
        "tags": ["technique", "beginner", "form"],
        "content": {
            "warmup": {"distance": 200, "description": "100м кроль спокойно + 100м на спине"},
            "main": {"sets": [
                {"repeat": 6, "distance": 100, "style": "кроль", "rest_sec": 30,
                 "note": "фокус на горизонтальное положение тела"},
            ]},
            "cooldown": {"distance": 200, "description": "спокойный кроль, растяжка в воде"},
            "total_distance": 1000,
            "coach_tip": "Сегодня следи за тем, чтобы бёдра не уходили вниз",
        },
    },
    {
        "level": "beginner", "type": "endurance", "duration_min": 30,
        "pool_meters": 50, "km_range": "1000",
        "tags": ["endurance", "beginner", "mixed"],
        "content": {
            "warmup": {"distance": 200, "description": "100м кроль + 100м брасс"},
            "main": {"sets": [
                {"repeat": 4, "distance": 100, "style": "кроль", "rest_sec": 45,
                 "note": "ровный темп, дыхание каждые 3 гребка"},
                {"repeat": 2, "distance": 100, "style": "брасс", "rest_sec": 45,
                 "note": "следи за правильным выдохом"},
            ]},
            "cooldown": {"distance": 200, "description": "спокойно на спине"},
            "total_distance": 1000,
            "coach_tip": "Контролируй дыхание — выдох должен быть полным",
        },
    },
    {
        "level": "beginner", "type": "recovery", "duration_min": 30,
        "pool_meters": 25, "km_range": "1000",
        "tags": ["recovery", "beginner", "easy"],
        "content": {
            "warmup": {"distance": 200, "description": "100м на спине + 100м брасс"},
            "main": {"sets": [
                {"repeat": 4, "distance": 150, "style": "любой стиль", "rest_sec": 60,
                 "note": "очень спокойный темп, наслаждайся движением"},
            ]},
            "cooldown": {"distance": 200, "description": "200м очень медленно, растяжка"},
            "total_distance": 1000,
            "coach_tip": "Цель сегодня — восстановление. Не спеши и дыши ровно",
        },
    },
    {
        "level": "beginner", "type": "technique", "duration_min": 45,
        "pool_meters": 25, "km_range": "1500",
        "tags": ["technique", "beginner", "backstroke"],
        "content": {
            "warmup": {"distance": 300, "description": "100м кроль + 100м на спине + 100м брасс"},
            "main": {"sets": [
                {"repeat": 6, "distance": 100, "style": "кроль", "rest_sec": 20,
                 "note": "фокус на вход руки — указательный палец первым"},
                {"repeat": 3, "distance": 100, "style": "на спине", "rest_sec": 30,
                 "note": "следи за прямым телом и ритмичным гребком"},
            ]},
            "cooldown": {"distance": 300, "description": "свободный стиль очень спокойно"},
            "total_distance": 1500,
            "coach_tip": "При кроле рука входит в воду на ширине плеча, не пересекая центр",
        },
    },
    {
        "level": "beginner", "type": "speed", "duration_min": 30,
        "pool_meters": 25, "km_range": "1000",
        "tags": ["speed", "beginner", "sprints"],
        "content": {
            "warmup": {"distance": 200, "description": "100м кроль + 100м на спине"},
            "main": {"sets": [
                {"repeat": 8, "distance": 50, "style": "кроль", "rest_sec": 30,
                 "note": "первые 4 отрезка 70% усилий, последние 4 — максимум"},
                {"repeat": 4, "distance": 50, "style": "на спине", "rest_sec": 30,
                 "note": "ровный темп, не торопись"},
            ]},
            "cooldown": {"distance": 200, "description": "спокойный кроль"},
            "total_distance": 1000,
            "coach_tip": "Скорость рождается из техники, а не из судорог",
        },
    },
    {
        "level": "beginner", "type": "endurance", "duration_min": 45,
        "pool_meters": 50, "km_range": "1500",
        "tags": ["endurance", "beginner", "50m"],
        "content": {
            "warmup": {"distance": 300, "description": "150м кроль + 150м брасс"},
            "main": {"sets": [
                {"repeat": 6, "distance": 150, "style": "кроль", "rest_sec": 30,
                 "note": "держи постоянный темп все 6 отрезков"},
            ]},
            "cooldown": {"distance": 300, "description": "свободный стиль, глубокое дыхание"},
            "total_distance": 1500,
            "coach_tip": "В 50м бассейне сосредоточься на повороте — оттолкнись сильнее",
        },
    },
    {
        "level": "beginner", "type": "recovery", "duration_min": 45,
        "pool_meters": 25, "km_range": "1500",
        "tags": ["recovery", "beginner", "mixed"],
        "content": {
            "warmup": {"distance": 300, "description": "100м кроль + 100м брасс + 100м на спине"},
            "main": {"sets": [
                {"repeat": 3, "distance": 200, "style": "кроль", "rest_sec": 60,
                 "note": "очень лёгкий темп"},
                {"repeat": 3, "distance": 100, "style": "брасс", "rest_sec": 60,
                 "note": "тяни удовольствие от воды"},
            ]},
            "cooldown": {"distance": 300, "description": "200м на спине + 100м кроль"},
            "total_distance": 1500,
            "coach_tip": "Восстановительная тренировка снимает усталость — не перегружайся",
        },
    },
    {
        "level": "beginner", "type": "technique", "duration_min": 45,
        "pool_meters": 50, "km_range": "1500",
        "tags": ["technique", "beginner", "breathing"],
        "content": {
            "warmup": {"distance": 300, "description": "100м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 5, "distance": 100, "style": "кроль", "rest_sec": 25,
                 "note": "дыши только влево — развиваем симметрию"},
                {"repeat": 4, "distance": 100, "style": "кроль", "rest_sec": 25,
                 "note": "дыши только вправо"},
            ]},
            "cooldown": {"distance": 300, "description": "300м вольный стиль, дыши по-разному"},
            "total_distance": 1500,
            "coach_tip": "Двустороннее дыхание сделает твой гребок симметричным",
        },
    },
    {
        "level": "beginner", "type": "speed", "duration_min": 45,
        "pool_meters": 50, "km_range": "1500",
        "tags": ["speed", "beginner", "pace"],
        "content": {
            "warmup": {"distance": 300, "description": "150м кроль + 150м брасс"},
            "main": {"sets": [
                {"repeat": 10, "distance": 50, "style": "кроль", "rest_sec": 25,
                 "note": "наращивай скорость каждые 2 отрезка"},
                {"repeat": 4, "distance": 100, "style": "кроль", "rest_sec": 40,
                 "note": "умеренный темп, восстановление"},
            ]},
            "cooldown": {"distance": 300, "description": "медленный кроль, растяжка"},
            "total_distance": 1500,
            "coach_tip": "Ускоряй ноги при спринте — они задают ритм",
        },
    },
    {
        "level": "beginner", "type": "endurance", "duration_min": 30,
        "pool_meters": 25, "km_range": "1000",
        "tags": ["endurance", "beginner", "continuous"],
        "content": {
            "warmup": {"distance": 200, "description": "100м кроль + 100м брасс"},
            "main": {"sets": [
                {"repeat": 8, "distance": 75, "style": "кроль", "rest_sec": 30,
                 "note": "ровный темп на протяжении всей серии"},
            ]},
            "cooldown": {"distance": 200, "description": "спокойно, любой стиль"},
            "total_distance": 1000,
            "coach_tip": "Постоянный темп тренирует выносливость лучше, чем рывки",
        },
    },

    # ── INTERMEDIATE ─────────────────────────────────────────────────────────
    {
        "level": "intermediate", "type": "technique", "duration_min": 45,
        "pool_meters": 25, "km_range": "1500",
        "tags": ["technique", "intermediate", "drill"],
        "content": {
            "warmup": {"distance": 300, "description": "150м кроль + 150м на спине"},
            "main": {"sets": [
                {"repeat": 6, "distance": 100, "style": "кроль (drill: catch-up)", "rest_sec": 20,
                 "note": "фокус на удлинённый гребок и высокий локоть"},
                {"repeat": 3, "distance": 100, "style": "кроль полный", "rest_sec": 20,
                 "note": "применяй технику из drills"},
            ]},
            "cooldown": {"distance": 300, "description": "свободный стиль, акцент на скольжение"},
            "total_distance": 1500,
            "coach_tip": "Drill catch-up: одна рука ждёт другую — учит тянуться вперёд",
        },
    },
    {
        "level": "intermediate", "type": "endurance", "duration_min": 60,
        "pool_meters": 50, "km_range": "2000",
        "tags": ["endurance", "intermediate", "aerobic"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 100м брасс + 100м на спине"},
            "main": {"sets": [
                {"repeat": 8, "distance": 150, "style": "кроль", "rest_sec": 20,
                 "note": "темп 75–80%, держи его без ускорений"},
            ]},
            "cooldown": {"distance": 400, "description": "200м на спине + 200м кроль спокойно"},
            "total_distance": 2000,
            "coach_tip": "Аэробная база строится только при умеренном темпе",
        },
    },
    {
        "level": "intermediate", "type": "speed", "duration_min": 45,
        "pool_meters": 25, "km_range": "1500",
        "tags": ["speed", "intermediate", "intervals"],
        "content": {
            "warmup": {"distance": 300, "description": "200м кроль + 100м брасс"},
            "main": {"sets": [
                {"repeat": 12, "distance": 50, "style": "кроль", "rest_sec": 25,
                 "note": "максимальная скорость, полное восстановление"},
                {"repeat": 3, "distance": 100, "style": "кроль", "rest_sec": 30,
                 "note": "умеренный темп — «заминка» внутри серии"},
            ]},
            "cooldown": {"distance": 300, "description": "спокойный кроль и брасс"},
            "total_distance": 1500,
            "coach_tip": "Интервалы 50м — лучший способ развить мощность гребка",
        },
    },
    {
        "level": "intermediate", "type": "recovery", "duration_min": 45,
        "pool_meters": 50, "km_range": "1500",
        "tags": ["recovery", "intermediate", "easy"],
        "content": {
            "warmup": {"distance": 300, "description": "100м кроль + 100м брасс + 100м на спине"},
            "main": {"sets": [
                {"repeat": 3, "distance": 300, "style": "любой стиль", "rest_sec": 60,
                 "note": "очень лёгкий темп, наслаждайся"},
            ]},
            "cooldown": {"distance": 300, "description": "300м вольный стиль с остановками"},
            "total_distance": 1500,
            "coach_tip": "После тяжёлой недели восстановление важнее нагрузки",
        },
    },
    {
        "level": "intermediate", "type": "technique", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["technique", "intermediate", "turns"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м комплекс"},
            "main": {"sets": [
                {"repeat": 8, "distance": 100, "style": "кроль с акцентом на повороты", "rest_sec": 20,
                 "note": "кувырок — отталкивание — скольжение 3 сек"},
                {"repeat": 4, "distance": 100, "style": "кроль", "rest_sec": 20,
                 "note": "применяй отработанный поворот"},
            ]},
            "cooldown": {"distance": 400, "description": "400м на спине медленно"},
            "total_distance": 2000,
            "coach_tip": "Хороший поворот экономит до 2 секунд на каждые 100м",
        },
    },
    {
        "level": "intermediate", "type": "endurance", "duration_min": 45,
        "pool_meters": 25, "km_range": "1500",
        "tags": ["endurance", "intermediate", "negative split"],
        "content": {
            "warmup": {"distance": 300, "description": "150м кроль + 150м брасс"},
            "main": {"sets": [
                {"repeat": 3, "distance": 300, "style": "кроль", "rest_sec": 30,
                 "note": "каждый следующий 300м на 2–3 сек быстрее предыдущего"},
            ]},
            "cooldown": {"distance": 300, "description": "300м вольный стиль"},
            "total_distance": 1500,
            "coach_tip": "Negative split: финиш быстрее старта — признак хорошей выносливости",
        },
    },
    {
        "level": "intermediate", "type": "speed", "duration_min": 60,
        "pool_meters": 50, "km_range": "2000",
        "tags": ["speed", "intermediate", "pyramid"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 1, "distance": 100, "style": "кроль", "rest_sec": 20, "note": "85%"},
                {"repeat": 1, "distance": 200, "style": "кроль", "rest_sec": 30, "note": "80%"},
                {"repeat": 1, "distance": 400, "style": "кроль", "rest_sec": 40, "note": "75%"},
                {"repeat": 1, "distance": 200, "style": "кроль", "rest_sec": 30, "note": "80%"},
                {"repeat": 1, "distance": 100, "style": "кроль", "rest_sec": 20, "note": "85%"},
            ]},
            "cooldown": {"distance": 400, "description": "400м спокойно, смешанные стили"},
            "total_distance": 2000,
            "coach_tip": "Пирамида учит правильно распределять усилия на дистанции",
        },
    },
    {
        "level": "intermediate", "type": "recovery", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["recovery", "intermediate", "technique focus"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 4, "distance": 300, "style": "любой стиль", "rest_sec": 60,
                 "note": "медленно, думай о технике каждого движения"},
            ]},
            "cooldown": {"distance": 400, "description": "400м очень медленно"},
            "total_distance": 2000,
            "coach_tip": "Медленное плавание с хорошей техникой строит правильные паттерны",
        },
    },
    {
        "level": "intermediate", "type": "endurance", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["endurance", "intermediate", "threshold"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м брасс"},
            "main": {"sets": [
                {"repeat": 6, "distance": 200, "style": "кроль", "rest_sec": 20,
                 "note": "темп чуть выше комфортного — пороговая зона"},
            ]},
            "cooldown": {"distance": 400, "description": "спокойный кроль с растяжкой"},
            "total_distance": 2000,
            "coach_tip": "Пороговые тренировки сдвигают анаэробный порог вверх",
        },
    },
    {
        "level": "intermediate", "type": "technique", "duration_min": 45,
        "pool_meters": 50, "km_range": "1500",
        "tags": ["technique", "intermediate", "stroke count"],
        "content": {
            "warmup": {"distance": 300, "description": "150м кроль + 150м брасс"},
            "main": {"sets": [
                {"repeat": 6, "distance": 100, "style": "кроль", "rest_sec": 20,
                 "note": "цель — снизить количество гребков на 25м на 1–2"},
                {"repeat": 3, "distance": 100, "style": "кроль", "rest_sec": 20,
                 "note": "сохраняй достигнутое количество гребков"},
            ]},
            "cooldown": {"distance": 300, "description": "300м свободно"},
            "total_distance": 1500,
            "coach_tip": "Меньше гребков при той же скорости = лучшее скольжение",
        },
    },

    # ── ADVANCED ─────────────────────────────────────────────────────────────
    {
        "level": "advanced", "type": "technique", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["technique", "advanced", "high elbow"],
        "content": {
            "warmup": {"distance": 500, "description": "200м кроль + 150м на спине + 150м брасс"},
            "main": {"sets": [
                {"repeat": 10, "distance": 100, "style": "кроль (drill: fingertip drag)", "rest_sec": 15,
                 "note": "пальцы скользят по поверхности — высокий локоть в пронесе"},
            ]},
            "cooldown": {"distance": 500, "description": "400м кроль + 100м брасс"},
            "total_distance": 2000,
            "coach_tip": "Высокий локоть в пронесе — основа мощного гребка у элиты",
        },
    },
    {
        "level": "advanced", "type": "endurance", "duration_min": 60,
        "pool_meters": 50, "km_range": "2500+",
        "tags": ["endurance", "advanced", "aerobic power"],
        "content": {
            "warmup": {"distance": 600, "description": "300м кроль + 150м на спине + 150м брасс"},
            "main": {"sets": [
                {"repeat": 11, "distance": 150, "style": "кроль", "rest_sec": 15,
                 "note": "темп 80%, ровный пульс на протяжении всей серии"},
            ]},
            "cooldown": {"distance": 550, "description": "300м кроль + 250м смешанные стили"},
            "total_distance": 2800,
            "coach_tip": "Длинные серии с коротким отдыхом — основа выносливости",
        },
    },
    {
        "level": "advanced", "type": "speed", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["speed", "advanced", "lactate"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 100м на спине + 100м брасс"},
            "main": {"sets": [
                {"repeat": 20, "distance": 50, "style": "кроль", "rest_sec": 20,
                 "note": "максимальный спринт каждый отрезок"},
                {"repeat": 2, "distance": 100, "style": "кроль", "rest_sec": 60,
                 "note": "восстановительный"},
            ]},
            "cooldown": {"distance": 400, "description": "400м свободно, очень медленно"},
            "total_distance": 2000,
            "coach_tip": "20×50м максимум накапливает лактат — учит его перерабатывать",
        },
    },
    {
        "level": "advanced", "type": "recovery", "duration_min": 60,
        "pool_meters": 50, "km_range": "2000",
        "tags": ["recovery", "advanced", "active rest"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 4, "distance": 300, "style": "любой стиль", "rest_sec": 60,
                 "note": "60% от максимума, думай только о технике"},
            ]},
            "cooldown": {"distance": 400, "description": "400м очень медленно, растяжка"},
            "total_distance": 2000,
            "coach_tip": "Активное восстановление ускоряет выведение лактата",
        },
    },
    {
        "level": "advanced", "type": "technique", "duration_min": 60,
        "pool_meters": 50, "km_range": "2500+",
        "tags": ["technique", "advanced", "tempo trainer"],
        "content": {
            "warmup": {"distance": 600, "description": "300м кроль + 300м смешанные стили"},
            "main": {"sets": [
                {"repeat": 7, "distance": 200, "style": "кроль", "rest_sec": 15,
                 "note": "держи фиксированную частоту гребков — 60–65 циклов/мин"},
            ]},
            "cooldown": {"distance": 600, "description": "600м вольный стиль"},
            "total_distance": 2600,
            "coach_tip": "Темп-тренер убирает колебания ритма и делает гребок стабильным",
        },
    },
    {
        "level": "advanced", "type": "endurance", "duration_min": 60,
        "pool_meters": 25, "km_range": "2000",
        "tags": ["endurance", "advanced", "threshold"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 6, "distance": 200, "style": "кроль", "rest_sec": 15,
                 "note": "пороговый темп — нельзя разговаривать, но можно дышать"},
            ]},
            "cooldown": {"distance": 400, "description": "400м спокойный кроль"},
            "total_distance": 2000,
            "coach_tip": "Порог — самая продуктивная зона для роста скоростной выносливости",
        },
    },
    {
        "level": "advanced", "type": "speed", "duration_min": 60,
        "pool_meters": 25, "km_range": "2500+",
        "tags": ["speed", "advanced", "race pace"],
        "content": {
            "warmup": {"distance": 500, "description": "200м кроль + 150м брасс + 150м на спине"},
            "main": {"sets": [
                {"repeat": 16, "distance": 100, "style": "кроль", "rest_sec": 20,
                 "note": "соревновательный темп — представь, что ты на старте"},
            ]},
            "cooldown": {"distance": 500, "description": "500м свободно"},
            "total_distance": 2600,
            "coach_tip": "Работа на соревновательном темпе строит психологическую устойчивость",
        },
    },
    {
        "level": "advanced", "type": "recovery", "duration_min": 60,
        "pool_meters": 50, "km_range": "2500+",
        "tags": ["recovery", "advanced", "easy distance"],
        "content": {
            "warmup": {"distance": 600, "description": "300м кроль + 300м смешанные стили"},
            "main": {"sets": [
                {"repeat": 7, "distance": 200, "style": "любой стиль", "rest_sec": 45,
                 "note": "50% интенсивности, думай о тянущихся движениях"},
            ]},
            "cooldown": {"distance": 600, "description": "600м очень медленно"},
            "total_distance": 2600,
            "coach_tip": "После соревнований первые 2 дня — только лёгкое плавание",
        },
    },
    {
        "level": "advanced", "type": "technique", "duration_min": 60,
        "pool_meters": 50, "km_range": "2000",
        "tags": ["technique", "advanced", "underwater"],
        "content": {
            "warmup": {"distance": 400, "description": "200м кроль + 200м на спине"},
            "main": {"sets": [
                {"repeat": 12, "distance": 100, "style": "кроль", "rest_sec": 15,
                 "note": "после каждого старта и поворота — 5 ударов дельфина под водой"},
            ]},
            "cooldown": {"distance": 400, "description": "400м свободно"},
            "total_distance": 2000,
            "coach_tip": "Подводный ход после поворота — самая быстрая фаза в кроле",
        },
    },
    {
        "level": "advanced", "type": "endurance", "duration_min": 60,
        "pool_meters": 25, "km_range": "2500+",
        "tags": ["endurance", "advanced", "volume"],
        "content": {
            "warmup": {"distance": 600, "description": "300м кроль + 300м смешанные стили"},
            "main": {"sets": [
                {"repeat": 8, "distance": 200, "style": "кроль", "rest_sec": 15,
                 "note": "ровный темп 75%, финиш с ускорением на последнем 200м"},
            ]},
            "cooldown": {"distance": 600, "description": "600м медленно, брасс и на спине"},
            "total_distance": 2800,
            "coach_tip": "Объёмная тренировка раз в неделю — фундамент для любой дистанции",
        },
    },
]


async def run_seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        existing = await session.execute(select(Workout))
        if existing.scalars().first():
            print("Workouts already seeded, skipping.")
            await engine.dispose()
            return

        for data in WORKOUTS:
            workout = Workout(**data)
            session.add(workout)

        await session.commit()
        print(f"Seeded {len(WORKOUTS)} workouts successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_seed())