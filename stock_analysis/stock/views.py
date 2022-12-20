from django.shortcuts import render
from .utils import NewsAggregator, save_in_db
from .models import News, Ticker
from datetime import datetime


def main_view(request):
    news_aggregator = NewsAggregator()
    if News.objects.first() and datetime.now().date() != News.objects.first().date_time.date():
        News.objects.all().delete()

    if request.method == 'GET':
        tickers = Ticker.objects.all()  # Получить тикер из формы
        last_news = dict()
        last_news['rbc'] = News.objects.filter(source=news_aggregator.source_rbc).first()
        last_news['finam'] = News.objects.filter(source=news_aggregator.source_finam).first()
        last_news['tg'] = News.objects.filter(source='tg').first()

        data = news_aggregator.aggregate(last_news, tickers)
        save_in_db(News, data)

        return render(request, 'stock/main.html', {'text': data})
