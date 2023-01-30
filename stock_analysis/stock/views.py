from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django import forms
from .utils import NewsAggregator, save_in_db, count_of_sentiment
from .utils import view_ticker_list
from .models import News, Ticker
from .forms import TickerSelectForm
from datetime import datetime


def main_view(request):
    news_aggregator = NewsAggregator()
    if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
        News.objects.all().delete()

    if request.method == 'GET':
        tickers = Ticker.objects.filter(ticker__in=view_ticker_list)
        last_news = dict()
        last_news['rbc'] = News.objects.filter(source=news_aggregator.source_rbc).first()
        last_news['finam'] = News.objects.filter(source=news_aggregator.source_finam).first()
        last_news['tg'] = News.objects.filter(source=news_aggregator.source_tg).first()

        data = news_aggregator.aggregate(last_news, tickers)
        save_in_db(News, data)

        sentiment_list = count_of_sentiment(view_ticker_list, News)

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

        return HttpResponseRedirect('/')

