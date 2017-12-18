# -*- coding: utf-8 -*-

# That's helpers very simple and pretend true way getting accounts any type
from card_issuing.constants import TRANSACTION_STATUSES
from card_issuing.models import Account
from ft_exec.settings import ACCOUNTS_MAPPING


def get_account_by_card_id(card_id):
    account_name = ACCOUNTS_MAPPING['card_id'].get(card_id)
    account = Account.objects.get(name=account_name)
    return account

def get_account_by_cardholder_name(cardholder_name):
    account_name = ACCOUNTS_MAPPING['cardholder'].get(cardholder_name)
    account = Account.objects.get(name=account_name)
    return account


def get_scheme_account():
    return Account.objects.get(id=6)


def get_bank_acount():
    return Account.objects.get(id=3)

def get_equity_account():
    return Account.objects.get(id=5)


def get_hold_amount(account, transaction_id):
    account_transfers_qs = account.get_transfers_by_transaction_external_id(transaction_id)
    account_transfer = account_transfers_qs.filter(transaction__status=TRANSACTION_STATUSES.HOLD).first()
    hold_anount = account_transfer.amount
    return hold_anount
