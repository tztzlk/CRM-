from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.utils import timezone

from clients.models import Client
from deals.models import Deal, Stage
from interactions.models import Interaction
from leads.models import Lead


def _leaderboard(month_start):
    """Compute top managers by composite score for current month."""
    rows = list(
        Deal.objects.filter(status='won', closed_at__gte=month_start)
        .values('owner__id', 'owner__username', 'owner__first_name', 'owner__last_name')
        .annotate(
            deals_closed=Count('id'),
            revenue=Sum('amount'),
        )
        .order_by('-revenue')[:10]
    )
    for i, row in enumerate(rows):
        # Composite points: deals * 100 + (revenue/10000 capped at 5000) * 0.3
        pts = row['deals_closed'] * 100 + min(int(float(row['revenue'] or 0) / 10000) * 3, 5000)
        row['points'] = pts
        row['rank'] = i + 1
        row['name'] = (
            f"{row['owner__first_name']} {row['owner__last_name']}".strip()
            or row['owner__username'] or '—'
        )
    rows.sort(key=lambda r: r['points'], reverse=True)
    for i, row in enumerate(rows):
        row['rank'] = i + 1
    return rows


@login_required
def dashboard(request):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    clients_count = Client.objects.count()
    deals_open = Deal.objects.filter(status='open').count()
    deals_this_month = Deal.objects.filter(created_at__gte=month_start).count()
    revenue_this_month = (
        Deal.objects.filter(status='won', closed_at__gte=month_start)
        .aggregate(s=Sum('amount'))['s'] or 0
    )

    recent_interactions = (
        Interaction.objects
        .select_related('client', 'author', 'deal')
        .order_by('-created_at')[:8]
    )

    mini_board = []
    for stage in Stage.objects.order_by('order'):
        mini_board.append({
            'stage': stage,
            'count': Deal.objects.filter(stage=stage, status='open').count(),
        })

    # AI Lead Priority stats
    hot_leads = Lead.objects.filter(priority='hot', status__in=['new', 'in_progress', 'qualified'])
    hot_count = hot_leads.count()

    threshold_30m = now - timedelta(minutes=30)
    hot_stale_count = hot_leads.filter(
        Q(first_contact_at__isnull=True) | Q(first_contact_at__lt=threshold_30m)
    ).count()

    leads_new_count = Lead.objects.filter(status='new').count()

    # Leaderboard
    leaderboard = _leaderboard(month_start)
    current_user_rank = next(
        (r['rank'] for r in leaderboard if r['owner__id'] == request.user.id), None
    )

    return render(request, 'core/dashboard.html', {
        'clients_count': clients_count,
        'deals_open': deals_open,
        'deals_this_month': deals_this_month,
        'revenue_this_month': revenue_this_month,
        'recent_interactions': recent_interactions,
        'mini_board': mini_board,
        'hot_count': hot_count,
        'hot_stale_count': hot_stale_count,
        'leads_new_count': leads_new_count,
        'leaderboard': leaderboard[:5],
        'current_user_rank': current_user_rank,
    })
