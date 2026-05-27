from django.contrib import admin
from .models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('type', 'subject', 'client', 'deal', 'author', 'created_at')
    list_filter = ('type', 'author')
    search_fields = ('subject', 'content', 'client__full_name')
