from django import forms
from .models import Interaction


class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = ('type', 'subject', 'content', 'deal')
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deal': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        if client is not None:
            self.fields['deal'].queryset = client.deals.all()
            self.fields['deal'].required = False
