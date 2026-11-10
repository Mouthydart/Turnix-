from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.blocked_periods import router as blocked_periods_router
from app.api.v1.routes.bookings import me_router as bookings_me_router
from app.api.v1.routes.bookings import router as bookings_router
from app.api.v1.routes.businesses import router as businesses_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.reviews import router as reviews_router
from app.api.v1.routes.services import router as services_router
from app.api.v1.routes.staff import router as staff_router
from app.api.v1.routes.staff_me import router as staff_me_router
from app.api.v1.routes.stats import router as stats_router
from app.api.v1.routes.waitlist import me_router as waitlist_me_router
from app.api.v1.routes.waitlist import router as waitlist_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["system"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(businesses_router, prefix="/businesses", tags=["businesses"])
api_router.include_router(services_router, prefix="/businesses", tags=["services"])
api_router.include_router(staff_router, prefix="/businesses", tags=["staff"])
api_router.include_router(bookings_router, prefix="/businesses", tags=["bookings"])
api_router.include_router(bookings_me_router, prefix="/bookings", tags=["bookings"])
api_router.include_router(
    blocked_periods_router, prefix="/businesses", tags=["blocked-periods"]
)
api_router.include_router(waitlist_router, prefix="/businesses", tags=["waitlist"])
api_router.include_router(waitlist_me_router, prefix="/waitlist", tags=["waitlist"])
api_router.include_router(staff_me_router, prefix="/staff", tags=["staff"])
api_router.include_router(reviews_router, prefix="/businesses", tags=["reviews"])
api_router.include_router(stats_router, prefix="/businesses", tags=["stats"])
