from django.shortcuts import render
from .utils import NewsAggregator, save_in_db
from .models import News, Ticker
from datetime import datetime


def main_view(request):
    news_aggregator = NewsAggregator()
    if News.objects.last() and \
            datetime.now().strftime("%Y-%m-%d") != \
            News.objects.first().date_time.strftime("%Y-%m-%d"):
        News.objects.all().delete()

    if request.method == 'GET':
        ticker = Ticker.objects.first()
        last_news_rss = News.objects.filter(source='rbc-news').first()
        last_news_tg = News.objects.filter(source='tg').first()
        last_news_site = News.objects.filter(source='finam').first()

        data_rss = news_aggregator.rss_parser(last_news_rss)

        # data = news_aggregator.tg_parser()
        # return render(request, 'stock/main.html', {'text': data})

        data_site = news_aggregator.site_parser(last_news_site)
        data_site.extend(data_rss)
        save_in_db(News, data_site, ticker)
        return render(request, 'stock/main.html', {'text': data_site})
