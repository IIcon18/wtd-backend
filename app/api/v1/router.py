from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    chat,
    history,
    payments,
    subscriptions,
    swim_profile,
    users,
    workouts,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(swim_profile.router)
router.include_router(chat.router)
router.include_router(history.router)
router.include_router(workouts.router)
router.include_router(subscriptions.router)
router.include_router(payments.router)
router.include_router(admin.router)