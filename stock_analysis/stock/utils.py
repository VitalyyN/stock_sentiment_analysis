import dotenv
import requests
import feedparser
from datetime import datetime
from dateutil.parser import parse
import emoji
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

dotenv.load_dotenv()


def create_dict_for_db(title, source, datetime_news, ticker):
    news_item = {'ticker': ticker,
                 'title': title,
                 'source': source,
                 'date_time': datetime_news}
    return news_item


def save_in_db(db_model, data_dict_list):
    for elem in data_dict_list:
        db_model.objects.create(ticker=elem['ticker'],
                                title=elem['title'],
                                source=elem['source'],
                                sentiment=1,  # Получить из анализа
                                date_time=elem['date_time'])


def check_news_by_key(key_list, text):
    for key in key_list:
        if text.find(key) != -1:
            return True
    return False


def check_news(news_all, ticker_db, title, datetime_news, source):
    for ticker_item in ticker_db:
        if datetime.now().date() == datetime_news.date() \
                and check_news_by_key(ticker_item.key_word.split(','), title):
            news_all.append(create_dict_for_db(title, source, datetime_news, ticker_item))


def rss_parser(url, source, last_news, ticker_db):
    res = requests.get(url)
    feed = feedparser.parse(res.text)
    news_all = list()

    for entry in feed.entries:
        title = None

        if source == 'rbc':
            title = entry['description'].lower()

        if source == 'finam':
            title = entry['title'].lower()

        if last_news and title.startswith(last_news.title[:40]):
            break

        datetime_news = parse(entry.published)
        check_news(news_all, ticker_db, title, datetime_news, source)

    return news_all


def tg_parser(url, source, last_news, ticker_db):
    news_all = list()
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--headless')
    driver = uc.Chrome(options=options)

    try:
        driver.get(url)
        news_list_all = driver.find_elements(By.CLASS_NAME, 'post-container')

        for elem in news_list_all:
            title = elem.find_element(By.CLASS_NAME, 'post-body').text
            title = ''.join(char for char in title if not emoji.is_emoji(char)).lower()

            if last_news and title.startswith(last_news.title[:40]):
                break

            datetime_news = parse(elem.find_element(By.CLASS_NAME, 'post-header').
                                  find_element(By.CLASS_NAME, 'text-muted').text)

            check_news(news_all, ticker_db, title, datetime_news, source)

        return news_all

    except Exception as ex:
        print(ex)
        return None
    finally:
        driver.close()
        driver.quit()


class NewsAggregator:
    def __init__(self, rbc=True, finam=True, tg=True):
        self.rss_link_rbc = 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss'
        self.rss_link_finam = 'https://www.finam.ru/analysis/conews/rsspoint/'
        self.tg_chanel = 'https://tgstat.ru/channel/@cbrstocks'

        self.source_finam = 'finam'
        self.source_rbc = 'rbc'
        self.source_tg = 'tg'

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
