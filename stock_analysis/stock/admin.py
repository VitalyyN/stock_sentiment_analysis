from django.contrib import admin
from .models import Ticker, History, News


class TickerAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticker', 'key_word']


class NewsAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticker', 'source', 'title', 'sentiment_label', 'sentiment_str',
                    'sentiment_score', 'date_time']


class HistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'positive_news', 'negative_news', 'date_history']


admin.site.register(Ticker, TickerAdmin)
admin.site.register(History, HistoryAdmin)
admin.site.register(News, NewsAdmin)
