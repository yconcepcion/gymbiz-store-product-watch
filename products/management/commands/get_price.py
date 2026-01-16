from django.core.management.base import BaseCommand

from products.utils.price_from_all import Price


class Command(BaseCommand):
    help = 'Get price from web'

    def handle(self, *args, **kwargs):

        price_helper = Price()
        price_helper.get_price_from_all()
