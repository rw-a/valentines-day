from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'ticketing'
urlpatterns = [
    path('', views.index, name='index'),

    path('redeem/', views.redeem, name='redeem'),
    path('redeemed/', views.redeemed, name='redeemed'),

    path('stats/', views.stats, name='stats'),
    path('timetables/', views.load_timetables, name='timetables'),
    path('timetables/success', views.timetables_loaded, name='timetables_done'),

    path('codes/<int:pk>', views.codepdf, name='codepdf'),
    path('tickets/<int:pk>', views.tickets, name='tickets'),
    path('tickets/<int:pk>/<str:group_id>', views.delivery_group, name='delivery_group'),

    path('api/redeem/', views.api_redeem, name='api_redeem'),
    path('validate_code/', views.validate_code, name='validate_code'),
    path('validate_recipient/', views.validate_recipient, name='validate_recipient'),
    path('print/', views.print_tickets, name='print'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
