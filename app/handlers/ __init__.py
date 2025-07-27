from .start import router as start_router
from .help import router as help_router
from .balance import router as balance_router
from .operations import router as operations_router
from .reports import router as reports_router
from .categories import router as categories_router
from .settings import router as settings_router
from .cancel import router as cancel_router

# Для main.py будет удобнее импортировать:
__all__ = [
    "start_router", "help_router", "balance_router",
    "operations_router", "reports_router",
    "categories_router", "settings_router", "cancel_router"
]