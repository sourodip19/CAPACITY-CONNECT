from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return _wrapped

    return decorator


def admin_required(view_func):
    return role_required("ADMIN")(view_func)


def trainer_required(view_func):
    return role_required("TRAINER")(view_func)


def student_required(view_func):
    return role_required("STUDENT")(view_func)
