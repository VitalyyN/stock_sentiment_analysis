from django.db import models


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
    sentiment = models.IntegerField(verbose_name='сентимен-анализ')
    date_time = models.DateTimeField(verbose_name='дата новости', null=True)

    class Meta:
        verbose_name = 'Новости'
        verbose_name_plural = 'Новости'
        ordering = ['-date_time']

    def __str__(self):
        return f'{self.ticker.ticker} - {self.title[:50]} - {str(self.sentiment)}'


class History(models.Model):
    ticker = models.ForeignKey(Ticker, verbose_name='Тикер', on_delete=models.CASCADE)
    positive_news = models.IntegerField(verbose_name='позитивные новости')
    negative_news = models.IntegerField(verbose_name='негативные новости')
    date_history = models.DateField(verbose_name='дата новости', null=True)

    class Meta:
        verbose_name = 'История'
        verbose_name_plural = 'Истоия'
        ordering = ['-date_history']

    def __str__(self):
        return f'{self.ticker} - pos: {str(self.positive_news)} - neg: {str(self.negative_news)} - {self.date_history}'
