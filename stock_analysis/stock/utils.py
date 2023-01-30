import dotenv
import re
import requests
import feedparser
from datetime import datetime
from dateutil.parser import parse
from bs4 import BeautifulSoup
from newspaper import Article
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from django.db.models import Count, F


dotenv.load_dotenv()

model = AutoModelForSequenceClassification.from_pretrained('stock/pt_save_pretrained')
tokenizer = AutoTokenizer.from_pretrained('stock/tokenizer_save_pretrained')
classifier = pipeline(task='sentiment-analysis', model=model, tokenizer=tokenizer)

labels_dict = {0: 'neutral', 1: 'positive', 2: 'negative'}

view_ticker_list = ['sber', 'gazp']


def count_of_sentiment(ticker_list, db_model):
    res_list = list()
    for ticker in ticker_list:
        query_set_filtered = db_model.objects.filter(ticker__ticker__exact=ticker)
        count_positive = query_set_filtered.filter(sentiment_label=1).count()
        count_negative = query_set_filtered.filter(sentiment_label=2).count()
        res_list.append({ticker: {'positive': count_positive, 'negative': count_negative}})

    return res_list


def sentiment_analise(clf, message):
    result = clf([message])
    sent_int = int(result[0]['label'][-1])
    return sent_int, labels_dict[sent_int], round(result[0]['score'], 2)


def create_dict_for_db(title, source, datetime_news, ticker, sentiment_int, sentiment_str, score):
    news_item = {'ticker': ticker,
                 'title': title,
                 'source': source,
                 'date_time': datetime_news,
                 'sentiment_int': sentiment_int,
                 'sentiment_str': sentiment_str,
                 'score': score}
    return news_item


def save_in_db(db_model, data_dict_list):
    for elem in data_dict_list:
        db_model.objects.create(ticker=elem['ticker'],
                                title=elem['title'],
                                source=elem['source'],
                                sentiment_label=elem['sentiment_int'],
                                sentiment_str=elem['sentiment_str'],
                                sentiment_score=elem['score'],
                                date_time=elem['date_time']
                                )


def check_news_by_key(key_list, text):
    for key in key_list:
        if text.find(key.strip()) != -1:
            return True
    return False


def check_news(news_all, ticker_db, title, datetime_news, source):
    for ticker_item in ticker_db:
        if datetime.now().date() == datetime_news.date() \
                and check_news_by_key(ticker_item.key_word.split(','), title):
            sent_int, sent_str, score = sentiment_analise(classifier, title)
            news_all.append(create_dict_for_db(title, source, datetime_news, ticker_item, sent_int, sent_str, score))


def rss_parser(url, source, last_news, ticker_db):
    res = requests.get(url)
    feed = feedparser.parse(res.text)
    news_all = list()

    for entry in feed.entries:
        title = None

        if source == 'rbc':
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", entry['description'].lower())

        if source == 'finam':
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", entry['title'].lower())

        if last_news and title.startswith(last_news.title[:40]):
            break

        datetime_news = parse(entry.published)
        check_news(news_all, ticker_db, title, datetime_news, source)

    return news_all


def tg_parser(url, source, last_news, ticker_db):
    news_all = list()
    article = Article(url)
    article.download()
    article.parse()
    soup = BeautifulSoup(article.html, 'lxml')
    news_list_all = soup.findAll(class_='post-container')

    for elem in news_list_all:
        try:
            title = elem.find(class_='post-text').text
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", title).lower()

            if last_news and title.startswith(last_news.title[:40]):
                break

            datetime_news = parse(elem.find(class_='text-muted').text)

            check_news(news_all, ticker_db, title, datetime_news, source)
        except AttributeError:
            continue

    return news_all


class NewsAggregator:
    rss_link_rbc = 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss'
    rss_link_finam = 'https://www.finam.ru/analysis/conews/rsspoint/'
    tg_chanel = 'https://tgstat.ru/channel/@cbrstocks'

    source_finam = 'finam'
    source_rbc = 'rbc'
    source_tg = 'tg'

    def __init__(self, rbc=True, finam=True, tg=True):
        self.rbc_available = rbc
        self.finam_available = finam
        self.tg_available = tg

    def aggregate(self, last_news, ticker_db):
        all_news = list()
        if self.rbc_available:
            news_rbc = rss_parser(self.rss_link_rbc, self.source_rbc, last_news[self.source_rbc], ticker_db)
            all_news.extend(news_rbc)
        if self.finam_available:
            news_finam = rss_parser(self.rss_link_finam, self.source_finam, last_news[self.source_finam],
                                    ticker_db)
            all_news.extend(news_finam)
        if self.tg_available:
            news_tg = tg_parser(self.tg_chanel, self.source_tg, last_news[self.source_tg], ticker_db)
            all_news.extend(news_tg)

        return all_news
