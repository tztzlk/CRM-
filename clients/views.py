from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Sum
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.permissions import EditorRequiredMixin
from .forms import ClientForm
from .models import Client


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.select_related('owner').annotate(
            deals_count=Count('deals'),
            deals_amount=Sum('deals__amount'),
        ).order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q)
                | Q(company__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
            )
        source = self.request.GET.get('source', '').strip()
        if source:
            qs = qs.filter(source=source)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['source'] = self.request.GET.get('source', '')
        ctx['source_choices'] = Client.Source.choices
        return ctx


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client = self.object
        ctx['deals'] = client.deals.select_related('stage', 'owner').all()
        ctx['interactions'] = client.interactions.select_related('author', 'deal').order_by('-created_at')
        return ctx


class ClientCreateView(EditorRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def form_valid(self, form):
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        messages.success(self.request, 'Клиент создан')
        return super().form_valid(form)


class ClientUpdateView(EditorRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Изменения сохранены')
        return super().form_valid(form)


class ClientDeleteView(EditorRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        messages.success(self.request, 'Клиент удалён')
        return super().form_valid(form)
