# -*- coding: utf-8 -*-


class ACCOUNT_TYPES(object):
    ASSET = 1
    LIABILITY = 2
    EQUITY = 3


class TRANSACTION_STATUSES(object):
    CANCELED = -1
    HOLD = 0
    PROCESSED = 1


class TRANSFER_STATUSES(object):
    DECLINED = -1
    PENDING = 0
    FINISHED = 1


class TRANSFER_TYPES(object):
    DEBIT = 1
    CREDIT = 2


class BALANCE_TYPES(object):
    LEDGER = 'ledger'
    AVAILABLE = 'available'


class MESSAGE_TYPES(object):
    AUTHORISATION = 'authorisation'
    PRESENTMENT = 'presentment'


TRANSACTION_BALANCE_MAPPING = {
    BALANCE_TYPES.LEDGER: TRANSACTION_STATUSES.PROCESSED,
    BALANCE_TYPES.AVAILABLE: TRANSACTION_STATUSES.HOLD
}