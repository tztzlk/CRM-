from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('export.csv', views.export_csv, name='export_csv'),
    path('leads-export.csv', views.export_leads_csv, name='export_leads_csv'),
]
