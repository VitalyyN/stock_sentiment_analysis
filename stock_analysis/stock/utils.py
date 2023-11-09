from typing import List, Dict, Type
import re
import requests
from datetime import datetime

from django.db.models import Count, QuerySet

import feedparser
import transformers
from loguru import logger
from dateutil.parser import parse
from bs4 import BeautifulSoup
from newspaper import Article
from newspaper.article import ArticleException
from requests import RequestException
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from .models import News

# create logger settings
logger.add(
    'logs/log.log',
    rotation='6h',
    compression='zip',
    level='INFO',
    format='{time} - {level} - {message}',
    backtrace=True,
    diagnose=True,
)

# create classifier for sentiment analyse
model = AutoModelForSequenceClassification.from_pretrained('stock/pt_save_pretrained')
tokenizer = AutoTokenizer.from_pretrained('stock/tokenizer_save_pretrained')
classifier = pipeline(task='sentiment-analysis', model=model, tokenizer=tokenizer)

# dict for translate sentiment labels
labels_dict = {0: 'neutral', 1: 'positive', 2: 'negative'}


class NewsAggregator:
    """
    Class aggregate news
    """
    rss_link_rbc: str = 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss'
    rss_link_finam: str = 'https://www.finam.ru/analysis/conews/rsspoint/'
    tg_chanel: str = 'https://tgstat.ru/channel/@cbrstocks'

    source_finam: str = 'finam'
    source_rbc: str = 'rbc'
    source_tg: str = 'tg'

    def __init__(self, rbc: bool = True, finam: bool = True, tg: bool = True):
        """
        Initial instance with necessary source for get news
        """
        self.rbc_available = rbc
        self.finam_available = finam
        self.tg_available = tg

    def aggregate(self, last_news: Dict, ticker_db: QuerySet):
        """
        Function parse sources and collect news if it contains information of ticker share
        """
        all_news = list()
        if self.rbc_available:
            # parse and collect news from rbc source
            news_rbc = rss_parser(self.rss_link_rbc, self.source_rbc, last_news[self.source_rbc], ticker_db)
            all_news.extend(news_rbc)
        if self.finam_available:
            # parse and collect news from finam source
            news_finam = rss_parser(self.rss_link_finam, self.source_finam, last_news[self.source_finam],
                                    ticker_db)
            all_news.extend(news_finam)
        if self.tg_available:
            # parse and collect news from tg source
            news_tg = tg_parser(self.tg_chanel, self.source_tg, last_news[self.source_tg], ticker_db)
            all_news.extend(news_tg)

        return all_news


def get_request(tickers: QuerySet, news_obj: Type[News], news_aggr: NewsAggregator, tickers_list: List[str]):
    """
    Function aggregate received news and return result of analysis
    """
    last_news = dict()

    # get last news from DB
    last_news['rbc'] = news_obj.objects.filter(source=news_aggr.source_rbc).only('title').first()
    last_news['finam'] = news_obj.objects.filter(source=news_aggr.source_finam).only('title').first()
    last_news['tg'] = news_obj.objects.filter(source=news_aggr.source_tg).only('title').first()

    # get news from sourses and save in DB
    data = news_aggr.aggregate(last_news, tickers)
    save_in_db(news_obj, data)

    # aggregate sentiment analysis for each tickers
    sentiment_list = count_of_sentiment(tickers_list, news_obj)
    return sentiment_list


@logger.catch
def count_of_sentiment(ticker_list: List[str], db_model: Type[News]):
    """
    Function get sentiment analysis from DB for each ticker
    """

    # get from DB aggregate result
    counts_sent = (db_model.objects.values('ticker__ticker', 'sentiment_label').
                   filter(ticker__ticker__in=ticker_list).
                   annotate(count_sent=Count('sentiment_label')).
                   filter(sentiment_label__in=[1, 2]))

    # create dict for data
    ticker_dict = {}
    for ticker in ticker_list:
        ticker_dict[ticker] = {'positive': 0, 'negative': 0}

    # filling dict data from DB
    for elem in counts_sent:
        ticker = elem.get('ticker__ticker')
        if elem.get('sentiment_label') == 1:
            ticker_dict[ticker]['positive'] = elem.get('count_sent')
        if elem.get('sentiment_label') == 2:
            ticker_dict[ticker]['negative'] = elem.get('count_sent')

    # return list of dicts with tickers and aggregate analysis
    res_list = [{key: value} for key, value in ticker_dict.items()]
    return res_list


@logger.catch
def sentiment_analise(clf: transformers.pipelines, message: str):
    """
    Function to do a sentiment analysis by NeuralNetwork classifier
    """
    result = clf([message])
    sent_int = int(result[0]['label'][-1])
    return sent_int, labels_dict[sent_int], round(result[0]['score'], 2)


@logger.catch
def create_dict_for_db(title: str,
                       source: str,
                       datetime_news: datetime,
                       ticker: str,
                       sentiment_int: int,
                       sentiment_str: str,
                       score: float):
    """
    Function for create dict for write in DB
    """
    news_item = {'ticker': ticker,
                 'title': title,
                 'source': source,
                 'date_time': datetime_news,
                 'sentiment_int': sentiment_int,
                 'sentiment_str': sentiment_str,
                 'score': score}
    return news_item


@logger.catch
def save_in_db(db_model: Type[News], data_dict_list: List):
    """
    Function for write data in DB
    """
    list_db_obj = []
    for elem in data_dict_list:
        db_elem = db_model(
            ticker=elem['ticker'],
            title=elem['title'],
            source=elem['source'],
            sentiment_label=elem['sentiment_int'],
            sentiment_str=elem['sentiment_str'],
            sentiment_score=elem['score'],
            date_time=elem['date_time']
        )
        list_db_obj.append(db_elem)
    db_model.objects.bulk_create(list_db_obj)


def check_news_by_key(key_list: List[str], text: str):
    """
    Function for check that keyword is in text
    """
    for key in key_list:
        if text.find(key.strip()) != -1:
            return True
    return False


@logger.catch
def check_news(news_all: List, ticker_db: QuerySet, title: str, datetime_news: datetime, source: str):
    """
    Function find news by keyword and date and save this news in list (news_all)
    """
    for ticker_item in ticker_db:
        if datetime.now().date() == datetime_news.date() \
                and check_news_by_key(ticker_item.key_word.split(','), title):
            sent_int, sent_str, score = sentiment_analise(classifier, title)
            news_all.append(create_dict_for_db(title, source, datetime_news, ticker_item, sent_int, sent_str, score))


def rss_parser(url: str, source: str, last_news: Type[News], ticker_db: QuerySet):
    """
    Function for parsing rss source. Return find news.
    """
    try:
        res = requests.get(url)
    except RequestException:
        logger.exception(f'Error by request {source}-sourse')
        return []

    # use feedparser for parsing
    feed = feedparser.parse(res.text)

    news_all = list()

    for entry in feed.entries:
        title = ''

        if source == 'rbc':
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", entry['description'].lower())

        if source == 'finam':
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", entry['title'].lower())

        if last_news and title.startswith(last_news.title[:40]):
            break

        datetime_news = parse(entry.published)

        # filtering news and save in DB
        check_news(news_all, ticker_db, title, datetime_news, source)

    return news_all


def tg_parser(url: str, source: str, last_news: Type[News], ticker_db: QuerySet):
    """
     Function for parsing tg source. Return find news.
     """
    news_all = list()
    article = Article(url)

    try:
        article.download()
        article.parse()
    except ArticleException as ae:
        logger.exception('Error while request tg-sourse')
        return news_all
    except Exception as e:
        logger.exception(e)
        return news_all

    # use BeautifulSoup for parsing
    soup = BeautifulSoup(article.html, 'lxml')
    news_list_all = soup.findAll(class_='post-container')

    for elem in news_list_all:
        try:
            title = elem.find(class_='post-text').text
            title = re.sub("[^А-Яа-яA-Za-z%0-9.,]", " ", title).lower()

            if last_news and title.startswith(last_news.title[:40]):
                break

            datetime_news = parse(elem.find(class_='text-muted').text)

            # filtering news and save in DB
            check_news(news_all, ticker_db, title, datetime_news, source)
        except AttributeError:
            logger.exception('Error while parse by BS tg-page')
            continue

    return news_all
