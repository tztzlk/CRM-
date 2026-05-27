from django.urls import path
from . import views

app_name = 'deals'

urlpatterns = [
    path('', views.DealListView.as_view(), name='list'),
    path('board/', views.board_view, name='board'),
    path('new/', views.DealCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DealDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.DealUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.DealDeleteView.as_view(), name='delete'),
    path('<int:pk>/move/', views.deal_move, name='move'),

    path('stages/', views.stage_list, name='stage_list'),
    path('stages/new/', views.stage_create, name='stage_create'),
    path('stages/<int:pk>/edit/', views.stage_edit, name='stage_edit'),
]
