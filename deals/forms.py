from django import forms
from .models import Deal, Stage


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = ('title', 'client', 'amount', 'stage', 'owner', 'expected_close_date', 'notes')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'expected_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ('name', 'order', 'is_won', 'is_lost', 'color')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_won': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_lost': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }
