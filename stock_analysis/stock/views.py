from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django import forms
from .utils import NewsAggregator, save_in_db, get_request
from .utils import view_ticker_list
from .models import News, Ticker
from .forms import TickerSelectForm
from datetime import datetime
import json


def main_view(request):
    news_aggregator = NewsAggregator()
    if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
        News.objects.all().delete()

    if request.method == 'GET':
        tickers = Ticker.objects.filter(ticker__in=view_ticker_list)
        sentiment_list, data = get_request(tickers, News, news_aggregator, view_ticker_list)

        form = TickerSelectForm()
        tickers_choice = Ticker.objects.all().order_by('ticker')
        choices = [(elem.ticker, elem.ticker) for elem in tickers_choice]
        choice_field = forms.ChoiceField(choices=choices, label='Выбирете тикер:')
        form.fields['ticker'] = choice_field

        return render(request, 'stock/main.html', {'text': data, 'tickers': tickers, 'form': form,
                                                   'sentiment': sentiment_list})

    else:
        ticker = request.POST.get('ticker')

        if ticker not in view_ticker_list:
            view_ticker_list.append(ticker)
            ticker_db = Ticker.objects.filter(ticker=ticker)
            sentiment_list, _ = get_request(ticker_db, News, news_aggregator, [ticker])
            return JsonResponse({'status': 1, 'ticker': ticker,
                                 'positive': sentiment_list[0].get(ticker).get('positive'),
                                 'negative': sentiment_list[0].get(ticker).get('negative')})

        return JsonResponse({'status': 0})


def ajax_delete_ticker(request):
    if request.method == 'POST':
        ticker = request.POST.get('ticker')
        view_ticker_list.remove(ticker)
        return JsonResponse({})


def ajax_update_data(request):
    if request.method == 'GET':
        news_aggregator = NewsAggregator()
        if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
            News.objects.all().delete()

        tickers = Ticker.objects.filter(ticker__in=view_ticker_list)
        sentiment_list, _ = get_request(tickers, News, news_aggregator, view_ticker_list)
        sentiment_dict = {'data': sentiment_list}

        return JsonResponse(sentiment_dict)
