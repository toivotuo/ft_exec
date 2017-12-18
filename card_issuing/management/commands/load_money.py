# -*- coding: utf-8 -*-
import requests
from decimal import Decimal
from django.conf import settings
from django.core.management import BaseCommand
from rest_framework.reverse import reverse_lazy

from card_issuing.models import Account
from card_issuing.utils import get_account_by_cardholder_name, get_bank_acount


class Command(BaseCommand):
    help = "Load money to account of cardholder name. Cardholder names are %s" % \
           settings.ACCOUNTS_MAPPING['card_id'].values()

    def add_arguments(self, parser):
        parser.add_argument('cardholder', nargs='+', type=str, help='cardholder name')
        parser.add_argument('amount', nargs=1, type=Decimal, help='amount of money')
        parser.add_argument('currency', nargs='?', type=str, help='Currency', default='EUR')

    def handle(self, *args, **options):
        for cardholder in options['cardholder']:
            try:
                account = get_account_by_cardholder_name(cardholder)
            except Account.DoesNotExist:
                self.stdout.write(self.style.ERROR('Account for this cardholder does not exist'))

            else:
                amount = options['amount'][0]
                response, current_amount = self._increase_amount_on_account(account, amount)
                self.stdout.write(self.style.SUCCESS('Successfully update account for cardholder'))
                if response.ok:
                    bank = get_bank_acount()
                    response, current_amount = self._increase_amount_on_account(bank, amount)
                self.stdout.write(self.style.SUCCESS('Successfully update account for the Bank'))

    def _build_headers(self, consumer_name='issuer'):
        auth_header_name = settings.API_AUTH_HEADER.replace('_', '-')
        auht_header_value = settings.API_CONSUMERS_AUTH_HEADERS[consumer_name]
        headers = {
            auth_header_name: auht_header_value
        }
        return headers

    def _increase_amount_on_account(self, account, amount):

        url = '{API_URL}{account_endpoint}'.format(**{
            'API_URL': settings.API_URL,
            'account_endpoint': reverse_lazy('api:accounts-detail', kwargs={'pk': account.id})
        })

        headers = self._build_headers()
        response = requests.get(url, headers=headers)
        primary_amount_available = Decimal(response.json()['amount_available'])
        primary_amount_ledger = Decimal(response.json()['amount_ledger'])
        current_amount_available = primary_amount_available + amount
        current_amount_ledger = primary_amount_ledger + amount

        response = requests.patch(url, data={'amount_available': current_amount_available,
                                             'amount_ledger': current_amount_ledger
                                             },
                                  headers=headers)
        return response, current_amount_available
