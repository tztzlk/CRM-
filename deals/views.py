import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.permissions import EditorRequiredMixin, role_required
from .forms import DealForm, StageForm
from .models import Deal, Stage


class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = 'deals/deal_list.html'
    context_object_name = 'deals'
    paginate_by = 25

    def get_queryset(self):
        qs = Deal.objects.select_related('client', 'stage', 'owner')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(client__full_name__icontains=q))
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        stage_id = self.request.GET.get('stage', '').strip()
        if stage_id.isdigit():
            qs = qs.filter(stage_id=int(stage_id))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['status'] = self.request.GET.get('status', '')
        ctx['stage'] = self.request.GET.get('stage', '')
        ctx['stages'] = Stage.objects.all()
        ctx['status_choices'] = Deal.Status.choices
        return ctx


class DealDetailView(LoginRequiredMixin, DetailView):
    model = Deal
    template_name = 'deals/deal_detail.html'
    context_object_name = 'deal'

    def get_queryset(self):
        return Deal.objects.select_related('client', 'stage', 'owner')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['interactions'] = self.object.interactions.select_related('author').order_by('-created_at')
        return ctx


class DealCreateView(EditorRequiredMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'deals/deal_form.html'

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get('client')
        if client_id:
            initial['client'] = client_id
        first = Stage.objects.order_by('order').first()
        if first:
            initial['stage'] = first.id
        return initial

    def form_valid(self, form):
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        form.instance.apply_stage_status()
        messages.success(self.request, 'Сделка создана')
        return super().form_valid(form)


class DealUpdateView(EditorRequiredMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'deals/deal_form.html'

    def form_valid(self, form):
        form.instance.apply_stage_status()
        messages.success(self.request, 'Изменения сохранены')
        return super().form_valid(form)


class DealDeleteView(EditorRequiredMixin, DeleteView):
    model = Deal
    template_name = 'deals/deal_confirm_delete.html'
    success_url = reverse_lazy('deals:list')


@login_required
def board_view(request):
    stages = Stage.objects.prefetch_related('deals__client', 'deals__owner').order_by('order')
    columns = []
    for stage in stages:
        deals = list(stage.deals.all())
        columns.append({
            'stage': stage,
            'deals': deals,
            'total': sum((d.amount or 0) for d in deals),
            'count': len(deals),
        })
    return render(request, 'deals/board.html', {'columns': columns})


@login_required
@require_POST
def deal_move(request, pk: int):
    if not request.user.can_edit():
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
    deal = get_object_or_404(Deal, pk=pk)
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('bad json')
    stage_id = payload.get('stage_id')
    if not stage_id:
        return HttpResponseBadRequest('stage_id required')
    stage = get_object_or_404(Stage, pk=int(stage_id))
    deal.stage = stage
    deal.apply_stage_status()
    deal.save()
    return JsonResponse({
        'ok': True,
        'deal_id': deal.id,
        'stage_id': stage.id,
        'status': deal.status,
    })


# Stage management (admin-only via decorator)
@role_required('admin')
def stage_list(request):
    stages = Stage.objects.all()
    return render(request, 'deals/stage_list.html', {'stages': stages})


@role_required('admin')
def stage_create(request):
    if request.method == 'POST':
        form = StageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Этап добавлен')
            from django.shortcuts import redirect
            return redirect('deals:stage_list')
    else:
        form = StageForm()
    return render(request, 'deals/stage_form.html', {'form': form})


@role_required('admin')
def stage_edit(request, pk: int):
    stage = get_object_or_404(Stage, pk=pk)
    if request.method == 'POST':
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            messages.success(request, 'Этап изменён')
            from django.shortcuts import redirect
            return redirect('deals:stage_list')
    else:
        form = StageForm(instance=stage)
    return render(request, 'deals/stage_form.html', {'form': form, 'stage': stage})
