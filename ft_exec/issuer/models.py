# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Q, Avg
from django.db.models.functions import Coalesce
from django.utils.translation import ugettext_lazy as _

from issuer.constants import TRANSACTION_STATUSES, TRANSFER_TYPES, BALANCE_TYPES, \
    ACCOUNT_TYPES, MESSAGE_TYPES, TRANSACTION_BALANCE_MAPPING


class Account(models.Model):
    TYPE_CHOICES = (
        (ACCOUNT_TYPES.ASSET, 'asset'),
        (ACCOUNT_TYPES.LIABILITY, 'liability'),
        (ACCOUNT_TYPES.EQUITY, 'equity'),
    )
    name = models.CharField(_("Name"), max_length=128)
    amount_available = models.DecimalField(_("Available Amount"), decimal_places=2, max_digits=12,
                                           default=Decimal("0.00"))
    amount_ledger = models.DecimalField(_("Ledger Amount"), decimal_places=2, max_digits=12,
                                        default=Decimal("0.00"))
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, blank=True)
    currency = models.CharField(_("Currency"), max_length=12, default="EUR")

    def __str__(self):
        return '{0} [{1}]'.format(self.name, self.amount_available)

    @property
    def sign(self):
        """
        check sign for account type.

         Assets = Liabilities + Equity ==>
            0 = Liabilities + Equity - Assets
        """
        sign_mapping = {
            ACCOUNT_TYPES.ASSET: -1,
            ACCOUNT_TYPES.EQUITY: 1,
            ACCOUNT_TYPES.LIABILITY: 1
        }
        return sign_mapping.get(self.type, 1)

    def get_balance(self, dt=None, balance_type=BALANCE_TYPES.AVAILABLE):
        """
        Return the balance for this account
        """
        transfers = self.transfers
        balance = getattr(self, 'amount_%s'% balance_type, 'amount_available')

        transaction_status = TRANSACTION_BALANCE_MAPPING[balance_type]
        if dt:
            transfers = transfers.filter(transaction__created_at__gte=dt,
                                         transaction__status=transaction_status)
            balance_delta = transfers.aggregate(summ=Coalesce(Sum('amount'), 0))['summ']
            balance += balance_delta * -self.sign

        return '%s %s' % (balance, self.currency)


    def transfer_to(self, to_account, amount, **transaction_kwargs):
        """
        Transfer money to another account
        """
        if to_account.sign == 1:
            direction = -1
        else:
            direction = 1

        transaction = Transaction.objects.create(**transaction_kwargs)
        Transfer.objects.create(transaction=transaction, account=self, amount=-amount * direction)
        Transfer.objects.create(transaction=transaction, account=to_account, amount=amount * direction)
        transaction.save()

        transaction_status = transaction_kwargs['status']
        self.amount_available -= amount
        to_account.amount_available += amount
        if transaction_status in (TRANSACTION_STATUSES.PROCESSED, ):
            self.amount_ledger -= amount
            to_account.amount_ledger += amount
        self.save()
        to_account.save()

        return transaction

    def get_transactions(self, dt=None):
        # TODO: implement for endpoint
        result = [tr.transaction for tr in self.transfers.all()]
        return result

    def get_transfers_by_transaction_external_id(self, external_id):
        return self.transfers.filter(transaction__external_transaction_id=external_id)


class Transaction(models.Model):
    STATUS_CHOICES = (
        (TRANSACTION_STATUSES.CANCELED, 'Canceled'),
        (TRANSACTION_STATUSES.HOLD, 'Drafted'),
        (TRANSACTION_STATUSES.PROCESSED, 'Processed'),
    )

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now_add=True)

    amount = models.DecimalField(max_digits=24, decimal_places=4,
                                 blank=True, null=True)
    external_transaction_id = models.CharField(_('Scheme transaction id'), max_length=12, null=True)
    status = models.SmallIntegerField(_("Transfer Status"), choices=STATUS_CHOICES)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        return "Transaction at {created_at}".format(created_at=self.created_at)

    def save(self, *args, **kwargs):
        # TODO: amount
        self.amount = self.transfers.aggregate(amount__avg=Avg('amount'))['amount__avg']
        super(Transaction, self).save(*args, **kwargs)


class Transfer(models.Model):
    account = models.ForeignKey(Account, related_name='transfers')
    amount = models.DecimalField(_("Amount"),
                                 decimal_places=2, max_digits=12,
                                 null=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now_add=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='transfers', verbose_name=_('Transactions'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Transfer")
        verbose_name_plural = _("Transfers")

    def __str__(self):
        return 'Transfer: {0} {1} [{2}]'.format(self.id, self.account, self.amount)

    @property
    def type(self):
        if self.amount < 0:
            return TRANSFER_TYPES.DEBIT
        elif self.amount > 0:
            return TRANSFER_TYPES.CREDIT


class SchemeMessage(models.Model):
    MESSAGE_TYPES_CHOICES = (
        (MESSAGE_TYPES.AUTHORISATION, MESSAGE_TYPES.AUTHORISATION),
        (MESSAGE_TYPES.PRESENTMENT, MESSAGE_TYPES.PRESENTMENT)
    )
    type = models.CharField(_('Message_types'), choices=MESSAGE_TYPES_CHOICES, max_length=12)
    card_id = models.CharField(_('Card ID'), max_length=8)
    transaction_id = models.CharField(_('Scheme Ttransaction ID'), max_length=12)
    merchant_name = models.CharField(_('Merchant Name'), max_length=128)
    merchant_country = models.CharField(_('Merchant Country'), max_length=4)
    merchant_mcc = models.SmallIntegerField(_('Merchant Category Code'))
    merchant_city = models.CharField(help_text='City of merchant', null=True, max_length=64)

    billing_amount = models.DecimalField(_("Billing amount"), decimal_places=2, max_digits=12, )
    billing_currency = models.CharField(_("Billing Currency"), max_length=12)
    transaction_amount = models.DecimalField(_("Transaction amount"), max_digits=12, decimal_places=2)
    transaction_currency = models.CharField(_("Transaction Currency"), max_length=12)
    settlement_amount = models.DecimalField(_("Settlement amount"), max_digits=12,
                                            decimal_places=2, null=True)
    settlement_currency = models.CharField(_("Settlement Currency"), max_length=12, null=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Scheme Message")
        verbose_name_plural = _("Scheme Messages")

        unique_together = ('type', 'transaction_id')
