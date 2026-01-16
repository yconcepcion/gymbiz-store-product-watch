from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from products.models import ApplicationToken


class ApplicationTokenAuthentication(BaseAuthentication):
    """
    Autenticación basada en token para aplicaciones
    """

    def authenticate(self, request):
        # Obtener el token del header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        # Verificar formato: Bearer <token>
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # Buscar token en la base de datos
            app_token = ApplicationToken.objects.select_related('user').get(
                token=token,
                is_active=True
            )

            # Actualizar última vez usado
            app_token.last_used = timezone.now()
            app_token.save(update_fields=['last_used'])

            return (app_token.user, app_token)

        except ApplicationToken.DoesNotExist:
            raise AuthenticationFailed('Token inválido o expirado')

    def authenticate_header(self, request):
        return 'Bearer'
