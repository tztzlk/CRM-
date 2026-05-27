from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from accounts.permissions import role_required
from clients.models import Client
from .forms import InteractionForm


@role_required('admin', 'manager')
def add_for_client(request, client_id: int):
    client = get_object_or_404(Client, pk=client_id)
    if request.method == 'POST':
        form = InteractionForm(request.POST, client=client)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.client = client
            obj.author = request.user
            obj.save()
            messages.success(request, 'Взаимодействие добавлено')
    return redirect('clients:detail', pk=client.id)


@role_required('admin', 'manager')
def delete_interaction(request, pk: int):
    from .models import Interaction
    obj = get_object_or_404(Interaction, pk=pk)
    client_id = obj.client_id
    obj.delete()
    messages.success(request, 'Запись удалена')
    return redirect('clients:detail', pk=client_id)
