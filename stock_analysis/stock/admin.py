from django.contrib import admin
from .models import Ticker, News, Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'watch_list']


class TickerAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticker', 'key_word']


class NewsAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticker', 'source', 'title', 'sentiment_label', 'sentiment_str',
                    'sentiment_score', 'date_time']


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Ticker, TickerAdmin)
admin.site.register(News, NewsAdmin)
