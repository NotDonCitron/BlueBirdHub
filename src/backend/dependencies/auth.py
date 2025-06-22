from src.backend.routes.auth import get_current_user, get_current_active_user

# Export authentication dependencies for use in other routes
__all__ = ["get_current_user", "get_current_active_user"]