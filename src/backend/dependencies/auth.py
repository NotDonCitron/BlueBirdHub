from src.backend.routes.auth import get_current_user, get_current_active_user
from src.backend.services.auth import verify_token

# Export authentication dependencies for use in other routes
__all__ = ["get_current_user", "get_current_active_user", "get_current_user_from_token", "verify_token"]

# Add alias for compatibility
get_current_user_from_token = get_current_active_user