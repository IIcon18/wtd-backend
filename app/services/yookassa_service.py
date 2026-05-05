"""YooKassa payment service."""
import logging
import uuid

from yookassa import Configuration, Payment
from yookassa.domain.notification import (
    WebhookNotificationEventType,
    WebhookNotificationFactory,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Prices in RUB — server-side only, never trust the client
TIER_PRICES: dict[str, int] = {
    "single": 149,
    "base": 299,
    "pro": 599,
}

TIER_DESCRIPTIONS: dict[str, str] = {
    "single": "Разовая тренировка WavesToDream",
    "base": "Подписка Base на 30 дней — WavesToDream",
    "pro": "Подписка Pro на 30 дней — WavesToDream",
}


def _configure() -> None:
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def get_tier_price(tier: str) -> int:
    return TIER_PRICES[tier]


def create_yookassa_payment(tier: str, user_id: int) -> dict:
    """Create a YooKassa payment and return yookassa_id + confirmation_url."""
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise RuntimeError("YooKassa credentials are not configured")

    _configure()
    price = TIER_PRICES[tier]
    return_url = f"{settings.FRONTEND_URL}/tariffs?payment=success"

    payment = Payment.create(
        {
            "amount": {"value": f"{price}.00", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": TIER_DESCRIPTIONS[tier],
            "metadata": {"user_id": str(user_id), "tier": tier},
        },
        str(uuid.uuid4()),  # idempotency key
    )

    logger.info(
        "Created YooKassa payment id=%s tier=%s user_id=%s price=%s",
        payment.id, tier, user_id, price,
    )
    return {
        "yookassa_id": payment.id,
        "confirmation_url": payment.confirmation.confirmation_url,
        "price": price,
    }


def check_payment_succeeded(yookassa_payment_id: str) -> bool:
    """Query YooKassa API and return True if the payment status is 'succeeded'."""
    _configure()
    payment = Payment.find_one(yookassa_payment_id)
    return payment.status == "succeeded"


def parse_webhook(body: bytes) -> tuple[str, str, str] | None:
    """
    Parse and validate an incoming YooKassa webhook.
    Returns (yookassa_payment_id, user_id, tier) on payment.succeeded,
    or None if the event is not payment.succeeded.
    """
    import json

    try:
        data = json.loads(body)
        notification = WebhookNotificationFactory().create(data)
    except Exception as exc:
        logger.warning("Failed to parse YooKassa webhook: %s", exc)
        raise ValueError("Invalid webhook payload") from exc

    if notification.event != WebhookNotificationEventType.PAYMENT_SUCCEEDED:
        logger.info("Ignoring YooKassa event: %s", notification.event)
        return None

    obj = notification.object
    metadata = obj.metadata or {}
    user_id = metadata.get("user_id")
    tier = metadata.get("tier")

    if not user_id or not tier:
        logger.error("Webhook missing metadata: %s", metadata)
        raise ValueError("Missing user_id or tier in payment metadata")

    return obj.id, user_id, tier
