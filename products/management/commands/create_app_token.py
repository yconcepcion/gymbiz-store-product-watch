from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from products.models import ApplicationToken


class Command(BaseCommand):
    help = 'Crea un token para una aplicación'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Nombre de usuario')
        parser.add_argument('--app-name', required=True, help='Nombre de la aplicación')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'])
            app_token = ApplicationToken.objects.create(
                user=user,
                app_name=options['app_name']
            )

            self.stdout.write(
                self.style.SUCCESS(f'Token creado exitosamente')
            )
            self.stdout.write(f'App: {app_token.app_name}')
            self.stdout.write(f'Token: {app_token.token}')
            self.stdout.write(f'Usuario: {user.username}')

        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR('Usuario no encontrado'))
