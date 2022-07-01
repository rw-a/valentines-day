from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'ticketing'
urlpatterns = [
    path('', views.index, name='index'),
    path('redeem/', views.purchase, name='purchase'),
    path('redeemed/', views.purchased, name='purchased'),
    path('validate_code/', views.validate_code, name='validate_code'),
    path('validate_recipient/', views.validate_recipient, name='validate_recipient'),
    path('codes/<int:pk>', views.codepdf, name='codepdf'),
    path('generator/', views.generator, name='generator'),
    path('generator/<str:code>/', views.generator),
    path('sort/', views.stats, name='stats')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
