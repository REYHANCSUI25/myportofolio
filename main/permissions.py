from rest_framework.permissions import SAFE_METHODS, BasePermission


class ModelPermissionOrReadOnly(BasePermission):
    model_name = ""
    actions = {"POST": "add", "PUT": "change", "PATCH": "change", "DELETE": "delete"}

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        action = self.actions.get(request.method)
        return action is not None and request.user.has_perm(
            f"main.{action}_{self.model_name}"
        )


class IsPortfolioOwnerOrEditorOrReadOnly(ModelPermissionOrReadOnly):
    message = "Your role can't perform this action on education entries."
    model_name = "education"


class IsPortfolioOwnerOrReadOnly(ModelPermissionOrReadOnly):
    message = "Your role can't perform this action on experience entries."
    model_name = "experience"
