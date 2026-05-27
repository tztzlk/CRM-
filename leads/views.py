import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.permissions import EditorRequiredMixin
from clients.models import Client
from deals.models import Deal, Stage
from .forms import LeadForm, LeadInteractionForm, ConvertLeadForm
from .models import Lead, LeadInteraction
from .scoring import LeadScorer


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 25

    def get_queryset(self):
        qs = Lead.objects.select_related('owner').order_by('-score', '-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q)
                | Q(company__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        source = self.request.GET.get('source', '').strip()
        if source:
            qs = qs.filter(source=source)
        priority = self.request.GET.get('priority', '').strip()
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['status'] = self.request.GET.get('status', '')
        ctx['source'] = self.request.GET.get('source', '')
        ctx['priority'] = self.request.GET.get('priority', '')
        ctx['status_choices'] = Lead.Status.choices
        ctx['source_choices'] = Lead.Source.choices
        ctx['priority_choices'] = Lead.Priority.choices

        # Hot leads banner: hot leads without interactions in last 30 min
        threshold = timezone.now() - timezone.timedelta(minutes=30)
        hot_stale = Lead.objects.filter(
            priority='hot',
            status__in=['new', 'in_progress', 'qualified'],
        ).filter(
            Q(first_contact_at__isnull=True) | Q(first_contact_at__lt=threshold)
        ).count()
        ctx['hot_stale_count'] = hot_stale
        return ctx


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lead = self.object
        scorer = LeadScorer()
        score, breakdown = scorer.calculate(lead)
        recommendation = scorer.build_recommendation(lead, breakdown)
        ctx['score_breakdown'] = breakdown
        ctx['recommendation'] = recommendation
        ctx['interaction_form'] = LeadInteractionForm()
        ctx['interactions'] = lead.interactions.select_related('author').order_by('-created_at')
        ctx['score_logs'] = lead.score_logs.order_by('-created_at')[:10]
        ctx['today'] = timezone.now().date()
        return ctx


class LeadCreateView(EditorRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'

    def form_valid(self, form):
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        messages.success(self.request, 'Лид создан')
        return super().form_valid(form)


class LeadUpdateView(EditorRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Лид обновлён')
        return super().form_valid(form)


class LeadDeleteView(EditorRequiredMixin, DeleteView):
    model = Lead
    template_name = 'leads/lead_confirm_delete.html'
    success_url = reverse_lazy('leads:list')

    def form_valid(self, form):
        messages.success(self.request, 'Лид удалён')
        return super().form_valid(form)


def lead_convert(request, pk):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if not request.user.can_edit():
        raise PermissionDenied

    lead = get_object_or_404(Lead, pk=pk)

    if lead.status == Lead.Status.CONVERTED:
        messages.warning(request, 'Этот лид уже конвертирован в клиента.')
        return redirect('leads:detail', pk=pk)

    if request.method == 'POST':
        form = ConvertLeadForm(request.POST)
        if form.is_valid():
            client = Client.objects.create(
                full_name=lead.full_name,
                company=lead.company,
                email=lead.email,
                phone=lead.phone,
                source=lead.source,
                notes=lead.notes,
                owner=lead.owner or request.user,
            )
            stage = form.cleaned_data['stage']
            deal = Deal(
                title=form.cleaned_data['deal_title'],
                client=client,
                amount=form.cleaned_data['deal_amount'] or 0,
                stage=stage,
                owner=lead.owner or request.user,
            )
            deal.apply_stage_status()
            deal.save()

            lead.status = Lead.Status.CONVERTED
            lead.converted_client = client
            lead.save()

            messages.success(
                request,
                f'Лид «{lead.full_name}» конвертирован: создан клиент и сделка «{deal.title}».'
            )
            return redirect('clients:detail', pk=client.pk)
    else:
        first_stage = Stage.objects.order_by('order').first()
        form = ConvertLeadForm(initial={
            'deal_title': f'Сделка: {lead.full_name}',
            'stage': first_stage,
            'deal_amount': lead.estimated_amount,
        })

    return render(request, 'leads/lead_convert.html', {'lead': lead, 'form': form})


# ── Lead interactions ─────────────────────────────────────────────────────────

@login_required
@require_POST
def add_interaction(request, pk):
    if not request.user.can_edit():
        raise PermissionDenied
    lead = get_object_or_404(Lead, pk=pk)
    form = LeadInteractionForm(request.POST)
    if form.is_valid():
        interaction = form.save(commit=False)
        interaction.lead = lead
        interaction.author = request.user
        interaction.save()
        messages.success(request, 'Взаимодействие добавлено')
    else:
        messages.error(request, 'Ошибка при добавлении взаимодействия')
    return redirect('leads:detail', pk=pk)


@login_required
@require_POST
def delete_interaction(request, pk):
    if not request.user.can_edit():
        raise PermissionDenied
    interaction = get_object_or_404(LeadInteraction, pk=pk)
    lead_pk = interaction.lead_id
    interaction.delete()
    # Recalculate score after deletion
    lead = get_object_or_404(Lead, pk=lead_pk)
    LeadScorer().update_lead(lead, reason='data_change')
    messages.success(request, 'Взаимодействие удалено')
    return redirect('leads:detail', pk=lead_pk)


# ── API endpoints ─────────────────────────────────────────────────────────────

@login_required
def api_score_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    scorer = LeadScorer()
    score, breakdown = scorer.calculate(lead)
    recommendation = scorer.build_recommendation(lead, breakdown)
    return JsonResponse({
        'score': score,
        'priority': lead.priority,
        'recommendation': recommendation,
        'breakdown': {
            k: {'label': v['label'], 'score': v['score'], 'max': v['max'], 'detail': v['detail']}
            for k, v in breakdown.items()
        },
    })


@login_required
@require_POST
def api_recalculate(request, pk):
    if not request.user.can_edit():
        raise PermissionDenied
    lead = get_object_or_404(Lead, pk=pk)
    score, _ = LeadScorer().update_lead(lead, reason='manual')
    return JsonResponse({'score': score, 'priority': lead.priority})


@login_required
def api_priority_distribution(request):
    from django.db.models import Count
    data = list(
        Lead.objects.values('priority').annotate(n=Count('id')).order_by('priority')
    )
    labels = {'hot': '🔥 Горячий', 'warm': '🟡 Тёплый', 'cold': '🔵 Холодный'}
    return JsonResponse({
        'labels': [labels.get(r['priority'], r['priority']) for r in data],
        'counts': [r['n'] for r in data],
    })


@login_required
def api_source_conversion(request):
    from django.db.models import Count
    rows = []
    for source_val, source_label in Lead.Source.choices:
        total = Lead.objects.filter(source=source_val).count()
        converted = Lead.objects.filter(source=source_val, status='converted').count()
        rows.append({
            'source': source_label,
            'total': total,
            'converted': converted,
            'rate': round(converted * 100 / total, 1) if total else 0,
        })
    return JsonResponse({'data': rows})
