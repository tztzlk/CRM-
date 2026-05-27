from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Allow only users whose .role is in roles (superusers always allowed)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            u = request.user
            if u.is_superuser or getattr(u, 'role', None) in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied('Недостаточно прав для выполнения операции')
        return _wrapped
    return decorator


class EditorRequiredMixin:
    """For CBVs: only admin/manager can access edit operations."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('accounts:login')
        if not request.user.can_edit():
            raise PermissionDenied('Недостаточно прав для редактирования')
        return super().dispatch(request, *args, **kwargs)
