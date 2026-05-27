from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('core.urls')),
    path('auth/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('leads/', include('leads.urls')),
    path('deals/', include('deals.urls')),
    path('interactions/', include('interactions.urls')),
    path('reports/', include('reports.urls')),
]

admin.site.site_header = 'CRM — Администрирование'
admin.site.site_title = 'CRM admin'
admin.site.index_title = 'Управление системой'
