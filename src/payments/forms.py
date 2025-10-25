from django import forms
from .models import Fee

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['amount', 'due_date', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }