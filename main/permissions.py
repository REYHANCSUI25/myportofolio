from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    message = "Your role can't perform this action on education entries."
    required_permissions = {
        "POST": "main.add_education",
        "PUT": "main.change_education",
        "PATCH": "main.change_education",
        "DELETE": "main.delete_education",
    }

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        permission = self.required_permissions.get(request.method)
        return permission is not None and request.user.has_perm(permission)
