from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'ticketing'
urlpatterns = [
    path('', views.page_index, name='index'),

    path('redeem/', views.page_redeem, name='redeem'),
    path('redeemed/', views.page_redeem_done, name='redeemed'),

    path('stats/', views.page_stats, name='stats'),
    path('timetables/', views.form_timetables, name='timetables'),
    path('timetables/success', views.page_timetables_loaded, name='timetables_done'),

    path('codes/<int:pk>', views.file_codepdf, name='codepdf'),
    path('tickets/<int:pk>', views.page_tickets, name='tickets'),
    path('tickets/<int:pk>/<str:group_id>/<int:part>', views.file_delivery_group, name='delivery_group'),

    path('api/redeem/', views.ApiRedeem.as_view(), name='api_redeem'),
    path('api/validate_code/', views.ApiRedeem.as_view(), name='api_validate_code'),
    path('api/print/', views.ApiPrintTicket.as_view(), name='api_print'),
    path('api/count', views.ApiCount.as_view(), name='api_count'),
    path('api/graph', views.ApiGraph.as_view(), name='api_graph'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
