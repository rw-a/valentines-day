from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'ticketing'
urlpatterns = [
    path('', views.index, name='index'),
    path('redeem/', views.redeem, name='redeem'),
    path('redeemed/', views.redeemed, name='redeemed'),
    path('validate_code/', views.validate_code, name='validate_code'),
    path('validate_recipient/', views.validate_recipient, name='validate_recipient'),
    path('codes/<int:pk>', views.codepdf, name='codepdf'),
    path('generator/', views.generator, name='generator'),
    path('generator/<str:code>/', views.generator),
    path('stats/', views.stats, name='stats')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
