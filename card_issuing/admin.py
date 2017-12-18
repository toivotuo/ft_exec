# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Account, Transfer, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    pass


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    #TODO: filters
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass
