# -*- coding: utf-8 -*-
import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum, F
from django.urls import reverse_lazy

from card_issuing.models import Transfer


class Command(BaseCommand):
    help = "Simulate Scheme's clearing process"

    def add_arguments(self, parser):
        parser.add_argument('-t, --transfer_ids', nargs='+', dest='ids',
                            type=list, help='Make transactions for transfer ids')

    def handle(self, *args, **options):

        url = '{API_URL}{clearing_endpoint}'.format(**{
            'API_URL': settings.API_URL,
            'clearing_endpoint': reverse_lazy('clearing')
        })

        headers = self._build_headers()
        response = requests.post(url, data={}, headers=headers)

        self.stdout.write(self.style.SUCCESS('Successfully made transactions for transfers'))

    def _build_headers(self, consumer_name='issuer'):
        auth_header_name = settings.API_AUTH_HEADER.replace('_', '-')
        auht_header_value = settings.API_CONSUMERS_AUTH_HEADERS[consumer_name]
        headers = {
            auth_header_name: auht_header_value
        }
        return headers
