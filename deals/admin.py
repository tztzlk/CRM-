from django.contrib import admin
from .models import Stage, Deal


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_won', 'is_lost', 'color')
    list_editable = ('order', 'is_won', 'is_lost', 'color')
    ordering = ('order',)


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'stage', 'status', 'amount', 'owner', 'created_at')
    list_filter = ('status', 'stage', 'owner')
    search_fields = ('title', 'client__full_name', 'client__company')
    autocomplete_fields = ('client',)
