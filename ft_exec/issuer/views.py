# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Sum
from drf_openapi.utils import view_config
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from issuer.constants import BALANCE_TYPES, TRANSACTION_STATUSES, MESSAGE_TYPES
from issuer.models import Account, SchemeMessage
from issuer.serializers import AuthMessageSerializer, PresentmentMessageSerializer, ResponseSerializer, \
    BalanceSerializer, AccountSerializer
from issuer.utils import get_account_by_card_id, get_bank_acount, get_scheme_account, get_hold_amount, \
    get_equity_account


class HasHeaderPermission(BasePermission):
    """
      Allows access only for consumers those who has API_AUTH_KEY header
    """

    def has_permission(self, request, view):
        auth_header = 'HTTP_' + settings.API_AUTH_HEADER
        allowed_headers = settings.API_CONSUMERS_AUTH_HEADERS.values()

        return (
            settings.DEBUG or
            auth_header in request.META and request.META[auth_header] in allowed_headers
        )


class BaseViewMixin(object):
    permission_classes = (HasHeaderPermission,)
    renderer_classes = (JSONRenderer, )


class ClearingView(BaseViewMixin, APIView):
    """
    A scheme-clearing endpoint for POST request.
    """

    def post(self, request):
        presented_messages = SchemeMessage.objects.filter(type=MESSAGE_TYPES.PRESENTMENT)
        aggrgate_summ = presented_messages.aggregate(biliable_sum=Sum('billing_amount'),
                                                     settlement_sum=Sum('settlement_amount'))
        amount_liability = aggrgate_summ['settlement_sum']
        amount_equity = aggrgate_summ['biliable_sum'] - aggrgate_summ['settlement_sum']

        fintech_ltd = get_equity_account()
        bank = get_bank_acount()
        scheme = get_scheme_account()
        now_timestamp = time.time()

        bank.transfer_to(scheme, amount=amount_liability, status=TRANSACTION_STATUSES.PROCESSED,
                         external_transaction_id=now_timestamp)
        bank.transfer_to(fintech_ltd, amount=amount_equity, status=TRANSACTION_STATUSES.PROCESSED,
                         external_transaction_id=now_timestamp)

        response_status = status.HTTP_200_OK
        return Response({"success": True,
                         'status_code': response_status,
                         'detail': ['liability: %s EUR' % amount_liability,'equity: %s EUR'% amount_equity]
                         }, status=response_status)


class AuthorisationMessageView(BaseViewMixin, GenericAPIView):
    """
    A scheme's webhook endpoint
    for authorisation message POST request.
    """

    serializer_class = AuthMessageSerializer

    def post(self, request):
        """
        Webhook for authorisation type of messages from scheme
        ---
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'success': False,
                             'status_code': status.HTTP_400_BAD_REQUEST,
                             'detail': serializer.errors
                             },
                            status=status.HTTP_400_BAD_REQUEST)

        data = serializer.initial_data

        card_id = data.get('card_id')
        external_transaction_id = data.get('transaction_id')
        billing_amount = Decimal(data.get('billing_amount'))

        account = get_account_by_card_id(card_id)
        bank = get_bank_acount()

        if billing_amount >= account.amount_available:
            response_status = status.HTTP_403_FORBIDDEN

            return Response({'success': False,
                             'status_code': response_status,
                             'detail': 'Need more gold'
                             },
                            status=response_status)
        try:
            with transaction.atomic():
                account.transfer_to(bank, amount=billing_amount, external_transaction_id=external_transaction_id,
                                    status=TRANSACTION_STATUSES.HOLD)
                serializer.save()
            response_status = status.HTTP_200_OK
            detail = 'Authorization success'
        except IntegrityError:
            response_status = status.HTTP_409_CONFLICT
            detail = 'Duplicated data'

        return Response({"success": True,
                         'status_code': response_status,
                         'detail': detail},
                        status=response_status)


class PresentmentMessageView(BaseViewMixin, GenericAPIView):
    """
    A scheme's webhook endpoint
    for presentment message POST request.
    """

    serializer_class = PresentmentMessageSerializer

  #  @view_config(request_serializer=PresentmentMessageSerializer, response_serializer=ResponseSerializer)
    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.initial_data
        card_id = data.get('card_id')
        billing_amount = Decimal(data.get('billing_amount'))

        transaction_id = data.get('transaction_id')
        account = get_account_by_card_id(card_id)
        bank = get_bank_acount()

        if billing_amount >= account.amount_ledger:
            response_status = status.HTTP_403_FORBIDDEN

            return Response({'success': False,
                             'status_code': response_status,
                             'detail': 'Need more gold'
                             },
                            status=response_status)
        try:
            with transaction.atomic():
                hold_amount = get_hold_amount(account, transaction_id)
                bank.transfer_to(account, hold_amount, status=TRANSACTION_STATUSES.CANCELED,
                                 external_transaction_id=transaction_id)
                account.transfer_to(bank, amount=billing_amount, status=TRANSACTION_STATUSES.PROCESSED,
                                    external_transaction_id=transaction_id)
                serializer.save()
            response_status = status.HTTP_200_OK
            detail = 'Authorization success'
            success = True
        except IntegrityError:
            success = False
            response_status = status.HTTP_409_CONFLICT
            detail = 'Duplicated data'

        return Response({"success": success,
                         'status_code': response_status,
                         'detail': detail},
                        status=response_status)


class CardholderBalanceView(BaseViewMixin, GenericAPIView):
    serializer_class = BalanceSerializer

    @view_config(request_serializer=BalanceSerializer, response_serializer=ResponseSerializer)
    def get(self, request, version):
        serializer = self.get_serializer(data=request.query_params)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'detail': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.initial_data
        dt = data.get('date_time', datetime.today())
        balance_type = data.get('balance_type', BALANCE_TYPES.AVAILABLE)
        account = get_account_by_card_id(data['card_id'])
        res = account.get_balance(dt=dt, balance_type=balance_type)

        return Response({"success": True,
                         "status_code": status.HTTP_200_OK,
                         "detail": res
                         }, status=status.HTTP_200_OK)


class AccountViewSet(BaseViewMixin, ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
