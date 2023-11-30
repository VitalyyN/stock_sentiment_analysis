from datetime import datetime

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login

from .utils import NewsAggregator, get_request
from .models import News, Ticker, Profile
from .forms import TickerSelectForm, LoginForm


class UserLogin(LoginView):
    form = LoginForm
    extra_context: {'form': form}


class UserLogout(LogoutView):
    template_name = 'registration/logout.html'


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def main_view(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/login')

    news_aggregator = NewsAggregator()
    if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
        News.objects.all().delete()

    if request.method == 'GET':
        view_ticker_list = request.user.profile.watch_list.split(', ')
        tickers = Ticker.objects.filter(ticker__in=view_ticker_list)

        sentiment_list = get_request(tickers, News, news_aggregator, view_ticker_list)

        form = TickerSelectForm()
        tickers_choice = Ticker.objects.all().order_by('ticker')
        choices = [(elem.ticker, elem.ticker) for elem in tickers_choice]
        choice_field = forms.ChoiceField(choices=choices, label='Выбирете тикер:',
                                         widget=forms.Select(attrs={"class": "form_select"}))
        form.fields['ticker'] = choice_field

        return render(request, 'stock/main.html', {'form': form,
                                                   'sentiment': sentiment_list, 'user': request.user})

    else:
        ticker = request.POST.get('ticker')
        view_ticker_list = request.user.profile.watch_list.split(', ')

        if ticker not in view_ticker_list:
            view_ticker_list.append(ticker)
            request.user.profile.watch_list = ', '.join(view_ticker_list)
            request.user.profile.save()

            ticker_db = Ticker.objects.filter(ticker=ticker)
            sentiment_list = get_request(ticker_db, News, news_aggregator, [ticker])
            return JsonResponse({'status': 1, 'ticker': ticker,
                                 'positive': sentiment_list[0].get(ticker).get('positive'),
                                 'negative': sentiment_list[0].get(ticker).get('negative')})

        return JsonResponse({'status': 0})


def ajax_delete_ticker(request):
    if request.method == 'POST':
        view_ticker = request.user.profile.watch_list
        view_ticker_list = list()
        if len(view_ticker) == 4:
            view_ticker_list.append(view_ticker)
        else:
            view_ticker_list = view_ticker.split(', ')

        ticker = request.POST.get('ticker')
        if len(view_ticker_list) == 1:
            return JsonResponse({'status': 1})

        view_ticker_list.remove(ticker)
        request.user.profile.watch_list = ', '.join(view_ticker_list)
        request.user.profile.save()

        return JsonResponse({'status': 0})


def ajax_update_data(request):
    if request.method == 'GET':
        news_aggregator = NewsAggregator()
        if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
            News.objects.all().delete()

        view_ticker = request.user.profile.watch_list
        view_ticker_list = list()
        if len(view_ticker) == 4:
            view_ticker_list.append(view_ticker)
        else:
            view_ticker_list = view_ticker.split(', ')

        tickers = Ticker.objects.filter(ticker__in=view_ticker_list)
        sentiment_list = get_request(tickers, News, news_aggregator, view_ticker_list)
        sentiment_dict = {'data': sentiment_list}

        return JsonResponse(sentiment_dict)
