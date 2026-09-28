from django.contrib.auth.decorators import login_required, permission_required

LOGIN_URL = "/login/"


def permission_required_or_403(perm):
    def decorator(view):
        guarded = permission_required(perm, raise_exception=True)(view)
        return login_required(login_url=LOGIN_URL)(guarded)

    return decorator
