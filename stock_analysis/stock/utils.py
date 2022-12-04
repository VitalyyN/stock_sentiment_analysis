import os
import dotenv
import requests
import feedparser
from datetime import datetime
import asyncio
from telethon.sync import TelegramClient
from telethon import utils
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


dotenv.load_dotenv()


def create_dict_for_db(title, source, date, time):
    news_item = {'title': title,
                 'source': source,
                 'date': date,
                 'time': time}
    return news_item


def save_in_db(db_model, data_dict, ticker):
    for elem in data_dict:
        db_model.objects.create(ticker=ticker,
                                title=elem['title'],
                                source=elem['source'],
                                sentiment=1,
                                date_time=datetime.strptime(f"{elem['date']} {elem['time']}", "%d.%m.%Y %H:%M:%S"))


class NewsAggregator:
    def __init__(self):
        self.rss_link = 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss'
        self.tg_chanel = '@cbrstocks'

        self.site = 'https://www.finam.ru/publications/section/companies/'

    def rss_parser(self, last_news):
        res = requests.get(self.rss_link)
        feed = feedparser.parse(res.text)
        news_all = list()
        source = 'rbc-news'

        for entry in feed.entries:
            title = entry['title']

            if last_news and title.startswith(last_news.title[:50]):
                break

            date = entry['rbc_news_date']
            time = entry['rbc_news_time']

            if datetime.now().date().strftime("%d.%m.%Y") == date:
                news_all.append(create_dict_for_db(title, source, date, time))

        return news_all

    def tg_parser(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        client = TelegramClient('scrapy',
                                int(os.getenv('TG_API_ID')),
                                os.getenv('TG_API_HASH')).start()
        chanel = client.get_entity(self.tg_chanel)
        # history = client.get_messages(chanel)
        history = client(GetHistoryRequest(
            peer=utils.get_input_peer(chanel),
            offset_id=0,
            offset_date=None,
            add_offset=0,
            limit=20,
            max_id=0,
            min_id=0,
            hash=0
        ))

        return history

    def site_parser(self, last_news):
        news_all = []
        source = 'finam'
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument('--headless')
        driver = uc.Chrome(options=options)

        try:
            driver.get(self.site)
            news_list_sel = driver.find_element(By.ID,
                                                'finfin-local-plugin-block-item-publication-list-filter-date-content')
            news = news_list_sel.find_elements(By.CLASS_NAME, 'publication-list-item')
            for elem in news:
                if elem.text[6].isdigit():
                    break
                if last_news and elem.text.startswith(last_news.title[:50]):
                    break
                news_dict = create_dict_for_db(title=elem.text,
                                               source=source,
                                               date=datetime.now().date().strftime("%d.%m.%Y"),
                                               time=f'{elem.text[:5]}:00')
                news_all.append(news_dict)
            return news_all
        except Exception as ex:
            print(ex)
            return None
        finally:
            driver.close()
            driver.quit()

