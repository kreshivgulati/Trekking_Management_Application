from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*allowed_roles):
    """
    Restricts a route to specific roles.
    Usage:
        @admin_bp.route('/dashboard')
        @login_required
        @role_required(RoleEnum.ADMIN)
        def dashboard():
            ...
    Must be stacked BELOW @login_required so current_user is guaranteed
    to be authenticated before this checks the role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator