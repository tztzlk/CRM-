from django.contrib import admin
from .models import Lead, LeadInteraction, LeadScoreLog, Achievement, ManagerStats, ManagerAchievement


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'company', 'phone', 'source', 'status',
        'score', 'priority', 'owner', 'created_at',
    ]
    list_filter = ['status', 'source', 'priority']
    search_fields = ['full_name', 'company', 'email', 'phone']
    readonly_fields = ['score', 'priority', 'score_updated_at', 'first_contact_at']
    autocomplete_fields = ['owner']


@admin.register(LeadInteraction)
class LeadInteractionAdmin(admin.ModelAdmin):
    list_display = ['lead', 'type', 'author', 'created_at']
    list_filter = ['type']
    autocomplete_fields = ['author']


@admin.register(LeadScoreLog)
class LeadScoreLogAdmin(admin.ModelAdmin):
    list_display = ['lead', 'score_before', 'score_after', 'reason', 'created_at']
    list_filter = ['reason']
    readonly_fields = ['lead', 'score_before', 'score_after', 'reason', 'created_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'slug', 'condition_code']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ManagerStats)
class ManagerStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'month', 'deals_closed', 'revenue', 'points']
    list_filter = ['month']


@admin.register(ManagerAchievement)
class ManagerAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
