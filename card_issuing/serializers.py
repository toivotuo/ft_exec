# -*- coding: utf-8 -*-
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_409_CONFLICT

from card_issuing.constants import TRANSFER_TYPES, TRANSFER_STATUSES, BALANCE_TYPES, MESSAGE_TYPES
from card_issuing.models import Transfer, Transaction, SchemeMessage, Account
from ft_exec.settings import ACCOUNTS_MAPPING


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = '__all__'


class TransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ('type', 'billing_amount', 'billing_currency', 'created_at', 'updated_at', 'status')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'



class CardIdMixin(object):
    card_id = serializers.CharField(help_text='Card id for chosen account')

    def validate_card_id(self, value):
        """
        This validation is very simple
        """
        if not ACCOUNTS_MAPPING['card_id'].get(value, ''):
            raise serializers.ValidationError("That card isn't supported our company")
        return value


class BaseMessageSerializer(CardIdMixin, serializers.ModelSerializer):
    """
    Base class for scheme messages
    """

    class Meta:
        model = SchemeMessage
        fields = '__all__'
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request',
            HTTP_403_FORBIDDEN: 'Forbidden',
            HTTP_409_CONFLICT: 'Conflict'
        }


class AuthMessageSerializer(BaseMessageSerializer):
    type = serializers.CharField(help_text='authorisation')

    def validate_type(self, value):
        if not value == MESSAGE_TYPES.AUTHORISATION:
            raise serializers.ValidationError("Wrong type")
        return value

    class Meta:
        model = SchemeMessage
        exclude = ('merchant_city', 'settlement_amount', 'settlement_currency')


class PresentmentMessageSerializer(BaseMessageSerializer):
    type = serializers.CharField(help_text='presentment')
    merchant_city = serializers.CharField(help_text='City of merchant', max_length=64)
    settlement_amount = serializers.DecimalField(help_text=("Settlement amount"), max_digits=12,
                                                 decimal_places=2)
    settlement_currency = serializers.CharField(help_text="Settlement Currency", max_length=12)

    def validate_type(self, value):
        if not value == 'presentment':
            raise serializers.ValidationError("Wrong type")
        return value


class ResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(help_text='Success or not')
    status_code = serializers.IntegerField(help_text='HTTP Response code')
    detail = serializers.CharField(help_text='Operation detail')


class BalanceSerializer(CardIdMixin, serializers.Serializer):
    date_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S',
                                          required=False,
                                          help_text='Point in time. Format: Y-m-dTH:M:S')
    _choices = (
        (BALANCE_TYPES.LEDGER, BALANCE_TYPES.LEDGER),
        (BALANCE_TYPES.AVAILABLE, BALANCE_TYPES.AVAILABLE)
    )
    balance_type = serializers.ChoiceField(choices=_choices, required=False)