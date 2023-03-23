from django import forms


class TickerSelectForm(forms.Form):
    ticker = forms.ChoiceField()


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
