from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # CRUD
    path('', views.LeadListView.as_view(), name='list'),
    path('add/', views.LeadCreateView.as_view(), name='create'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.LeadUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.LeadDeleteView.as_view(), name='delete'),
    path('<int:pk>/convert/', views.lead_convert, name='convert'),

    # Interactions
    path('<int:pk>/interaction/add/', views.add_interaction, name='add_interaction'),
    path('interaction/<int:pk>/delete/', views.delete_interaction, name='delete_interaction'),

    # API
    path('api/<int:pk>/score/', views.api_score_detail, name='api_score'),
    path('api/<int:pk>/recalculate/', views.api_recalculate, name='api_recalculate'),
    path('api/priority-distribution/', views.api_priority_distribution, name='api_priority_dist'),
    path('api/source-conversion/', views.api_source_conversion, name='api_source_conversion'),
]
