from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path('client/<int:client_id>/add/', views.add_for_client, name='add_for_client'),
    path('<int:pk>/delete/', views.delete_interaction, name='delete'),
]
