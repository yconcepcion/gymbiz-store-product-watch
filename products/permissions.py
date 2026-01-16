from rest_framework.permissions import BasePermission

from products.models import ApplicationToken


class IsApplicationAuthenticated(BasePermission):
    """
    Permite acceso solo a aplicaciones autenticadas con token
    """

    def has_permission(self, request, view):
        return hasattr(request, 'auth') and isinstance(request.auth, ApplicationToken)