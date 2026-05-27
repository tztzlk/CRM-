from clients.models import Client
from deals.models import Deal
from leads.models import Lead


def nav_counters(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'nav_clients_count': Client.objects.count(),
        'nav_deals_open': Deal.objects.filter(status='open').count(),
        'nav_leads_new': Lead.objects.filter(status__in=['new', 'in_progress', 'qualified']).count(),
    }
