from app.handlers.start import router as start_router
from app.handlers.profile import router as profile_router
from app.handlers.top import router as top_router
from app.handlers.admin import router as admin_router
from app.handlers.group import router as group_router
from app.handlers.utils import router as utils_router


def setup_routers() -> list:
    return [
        start_router,
        profile_router,
        top_router,
        admin_router,
        group_router,
        utils_router,
    ]
