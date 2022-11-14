from django.db import models


class Ticker(models.Model):
    ticker = models.CharField(max_length=10, verbose_name='Тикер', default='')

    class Meta:
        verbose_name = 'Тикер'
        verbose_name_plural = 'Тикеры'

    def __str__(self):
        return self.ticker


class News(models.Model):
    ticker = models.ForeignKey(Ticker, verbose_name='Тикер', on_delete=models.CASCADE)
    title = models.TextField(verbose_name='Заголовок', default='')
    sentiment = models.IntegerField(verbose_name='сентимен-анализ')
    date = models.DateField(verbose_name='дата новости', auto_now_add=True, null=True)
    time = models.TimeField(verbose_name='время добавления', auto_now_add=True, null=True)

    class Meta:
        verbose_name = 'Новости'
        verbose_name_plural = 'Новости'

    def __str__(self):
        return f'{self.ticker} - {self.title[:50]} - {str(self.sentiment)}'


class History(models.Model):
    ticker = models.ForeignKey(Ticker, verbose_name='Тикер', on_delete=models.CASCADE)
    positive_news = models.IntegerField(verbose_name='позитивные новости')
    negative_news = models.IntegerField(verbose_name='негативные новости')
    date_history = models.DateField(verbose_name='дата новости', null=True)

    class Meta:
        verbose_name = 'История'
        verbose_name_plural = 'Истоия'

    def __str__(self):
        return f'{self.ticker} - pos: {str(self.positive_news)} - neg: {str(self.negative_news)} - {self.date_history}'
