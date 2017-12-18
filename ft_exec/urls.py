from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers, renderers

from card_issuing import views


router = routers.DefaultRouter()
router.register(r'accounts', views.AccountViewSet,
                base_name='accounts')

API_PREFIX = r'^v(?P<version>[0-9]+\.[0-9]+)'
urlpatterns = [
    # url(r'^$', schema_view),
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/', include(router.urls, namespace='api')),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^api/v1/operations/clearing/$', views.ClearingView.as_view(),
        name='clearing'),
    url(r'^api/v1/operations/auth/$', views.AuthorisationMessageView.as_view(),
        name='auth'),
    url(r'^api/v1/operations/presentment/$', views.PresentmentMessageView.as_view(),
        name='presentment'),
    url(r'^api/v1/operations/balance/$', views.CardholderBalanceView.as_view(),
        name='balance'),

    url(r'^v(?P<version>[0-9]+\.[0-9]+)', include('drf_openapi.urls'))
    ]
