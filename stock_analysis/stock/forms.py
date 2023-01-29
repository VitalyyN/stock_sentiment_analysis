from django import forms
from .models import Ticker


class TickerSelectForm(forms.Form):
    ticker = forms.ChoiceField()
