import csv
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from deals.models import Deal, Stage
from leads.models import Lead


def _parse_date(value: str):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _filtered_deals(request):
    qs = Deal.objects.all()
    start = _parse_date(request.GET.get('start', ''))
    end = _parse_date(request.GET.get('end', ''))
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    return qs, start, end


@login_required
def index(request):
    deals, start, end = _filtered_deals(request)

    by_status = {row['status']: row['n'] for row in deals.values('status').annotate(n=Count('id'))}
    won = by_status.get('won', 0)
    lost = by_status.get('lost', 0)
    open_ = by_status.get('open', 0)
    total = won + lost + open_
    conversion = round(won * 100 / (won + lost), 1) if (won + lost) else 0.0

    by_stage_qs = (
        Stage.objects.annotate(
            n=Count('deals', filter=Q(deals__in=deals)),
            amount=Sum('deals__amount', filter=Q(deals__in=deals)),
        ).order_by('order').values('name', 'color', 'n', 'amount')
    )
    by_stage = [
        {'name': r['name'], 'color': r['color'], 'n': r['n'], 'amount': float(r['amount'] or 0)}
        for r in by_stage_qs
    ]

    by_month_qs = (
        deals.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(n=Count('id'), amount=Sum('amount'))
        .order_by('month')
    )
    by_month = [
        {
            'month': row['month'].strftime('%Y-%m') if row['month'] else '',
            'n': row['n'],
            'amount': float(row['amount'] or 0),
        }
        for row in by_month_qs
    ]

    top_managers = list(
        deals.filter(status='won')
        .values('owner__id', 'owner__username', 'owner__first_name', 'owner__last_name')
        .annotate(n=Count('id'), amount=Sum('amount'))
        .order_by('-amount')[:5]
    )

    total_revenue = deals.filter(status='won').aggregate(s=Sum('amount'))['s'] or 0

    # ── AI Lead Priority analytics ────────────────────────────────────────────

    # Hot leads without activity more than 1 hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    hot_stale_leads = Lead.objects.filter(
        priority='hot',
        status__in=['new', 'in_progress', 'qualified'],
    ).filter(
        Q(first_contact_at__isnull=True) | Q(first_contact_at__lt=one_hour_ago)
    ).select_related('owner').order_by('-score')[:10]

    # Priority distribution
    priority_dist_qs = Lead.objects.values('priority').annotate(n=Count('id'))
    priority_labels = {'hot': '🔥 Горячий', 'warm': '🟡 Тёплый', 'cold': '🔵 Холодный'}
    priority_dist = [
        {'label': priority_labels.get(r['priority'], r['priority']), 'n': r['n'], 'priority': r['priority']}
        for r in priority_dist_qs
    ]

    # Conversion by source
    source_conversion = []
    for source_val, source_label in Lead.Source.choices:
        total_src = Lead.objects.filter(source=source_val).count()
        converted_src = Lead.objects.filter(source=source_val, status='converted').count()
        source_conversion.append({
            'source': source_label,
            'total': total_src,
            'converted': converted_src,
            'rate': round(converted_src * 100 / total_src, 1) if total_src else 0,
        })

    # Average response time by manager (from first_contact_at - created_at on leads)
    avg_response_qs = (
        Lead.objects
        .filter(first_contact_at__isnull=False)
        .values('owner__username', 'owner__first_name', 'owner__last_name')
        .annotate(leads_n=Count('id'))
        .order_by('owner__username')[:10]
    )

    return render(request, 'reports/index.html', {
        'start': start.isoformat() if start else '',
        'end': end.isoformat() if end else '',
        'total': total,
        'won': won,
        'lost': lost,
        'open': open_,
        'conversion': conversion,
        'total_revenue': total_revenue,
        'by_stage': by_stage,
        'by_month': by_month,
        'top_managers': top_managers,
        # AI widgets
        'hot_stale_leads': hot_stale_leads,
        'priority_dist': priority_dist,
        'source_conversion': source_conversion,
    })


@login_required
def export_csv(request):
    deals, _, _ = _filtered_deals(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="deals.csv"'
    response.write('﻿')  # BOM for Excel
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'Название', 'Клиент', 'Этап', 'Статус',
        'Сумма', 'Ответственный', 'Создана',
    ])
    for d in deals.select_related('client', 'stage', 'owner'):
        writer.writerow([
            d.id, d.title, d.client.full_name, d.stage.name,
            d.get_status_display(), d.amount,
            (d.owner.get_full_name() or d.owner.username) if d.owner else '',
            d.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response


@login_required
def export_leads_csv(request):
    """Export leads with AI scoring data."""
    leads = Lead.objects.select_related('owner').order_by('-score')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="leads_scoring.csv"'
    response.write('﻿')
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID', 'ФИО', 'Компания', 'Телефон', 'Email',
        'Источник', 'Статус', 'AI-балл', 'Приоритет',
        'Потенциальная сумма', 'Ответственный', 'Создан',
    ])
    for lead in leads:
        writer.writerow([
            lead.id, lead.full_name, lead.company, lead.phone, lead.email,
            lead.get_source_display(), lead.get_status_display(),
            lead.score, lead.get_priority_display(),
            lead.estimated_amount or '',
            (lead.owner.get_full_name() or lead.owner.username) if lead.owner else '',
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response
