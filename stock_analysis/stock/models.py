from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    watch_list = models.CharField(max_length=100, verbose_name='Список наблюдения', default='gazp, sber')

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователя'

    def __str__(self):
        return f'{self.user}, {self.watch_list}'


class Ticker(models.Model):
    ticker = models.CharField(max_length=10, verbose_name='Тикер', default='')
    key_word = models.CharField(max_length=300, verbose_name='ключевые слова', default='')

    class Meta:
        verbose_name = 'Тикер'
        verbose_name_plural = 'Тикеры'

    def __str__(self):
        return self.ticker


class News(models.Model):
    ticker = models.ForeignKey(Ticker, verbose_name='Тикер', on_delete=models.CASCADE)
    title = models.TextField(verbose_name='Заголовок', default='')
    source = models.CharField(max_length=50, verbose_name='источник', default='')
    sentiment_label = models.IntegerField(verbose_name='лейбл', default=0)
    sentiment_str = models.CharField(max_length=15, verbose_name='сентимен-анализ', default='')
    sentiment_score = models.DecimalField(verbose_name='уверенность анализа', default=0, max_digits=3, decimal_places=2)
    date_time = models.DateTimeField(verbose_name='дата новости', null=True)

    class Meta:
        verbose_name = 'Новости'
        verbose_name_plural = 'Новости'
        ordering = ['-date_time']

    def __str__(self):
        return f'{self.ticker.ticker} - {self.title[:50]} - {self.sentiment_str}'
