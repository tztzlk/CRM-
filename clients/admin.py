from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company', 'phone', 'email', 'source', 'owner', 'created_at')
    list_filter = ('source', 'owner')
    search_fields = ('full_name', 'company', 'email', 'phone')
