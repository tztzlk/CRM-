from django import forms
from .models import Lead, LeadInteraction


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            # Контакт
            'full_name', 'position', 'phone', 'phone_alt', 'email',
            'telegram', 'contact_preference',
            # Компания
            'company', 'industry', 'company_size', 'city', 'website',
            # Сделка
            'source', 'status', 'product_interest',
            'estimated_amount', 'deal_urgency', 'next_contact_date',
            # Управление
            'owner', 'notes',
            # AI
            'response_speed_hours',
            # UTM
            'utm_source', 'utm_medium', 'utm_campaign',
        ]
        widgets = {
            'product_interest': forms.Textarea(attrs={'rows': 3,
                'placeholder': 'Что ищет клиент, какая задача, боль или вопрос...'}),
            'notes': forms.Textarea(attrs={'rows': 3,
                'placeholder': 'Дополнительные заметки о лиде...'}),
            'estimated_amount': forms.NumberInput(attrs={'placeholder': 'например: 150000'}),
            'response_speed_hours': forms.NumberInput(attrs={
                'placeholder': 'среднее время ответа клиента в часах', 'step': '0.5',
            }),
            'next_contact_date': forms.DateInput(attrs={'type': 'date'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
            'telegram': forms.TextInput(attrs={'placeholder': '@username'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
            'phone_alt': forms.TextInput(attrs={'placeholder': '+7 (999) 765-43-21'}),
        }


class LeadInteractionForm(forms.ModelForm):
    class Meta:
        model = LeadInteraction
        fields = ['type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2, 'placeholder': 'Описание взаимодействия...',
            }),
        }


class ConvertLeadForm(forms.Form):
    deal_title = forms.CharField(
        label='Название сделки',
        max_length=200,
        help_text='Будет создана сделка с этим названием',
    )
    deal_amount = forms.DecimalField(
        label='Сумма сделки',
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=14,
        help_text='Оставьте пустым, если сумма неизвестна',
    )
    stage = forms.ModelChoiceField(
        label='Начальный этап воронки',
        queryset=None,
    )

    def __init__(self, *args, **kwargs):
        from deals.models import Stage
        super().__init__(*args, **kwargs)
        self.fields['stage'].queryset = Stage.objects.order_by('order')
