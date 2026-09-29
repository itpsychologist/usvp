import datetime

from django.contrib.syndication.views import Feed
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed


class NewsFeed(Feed):
    """RSS останніх 20 новин (лише посилання й анонс, без зовнішніх сервісів)."""

    feed_type = Rss201rev2Feed

    def __init__(self, index_page):
        super().__init__()
        self.index_page = index_page

    def __call__(self, request, *args, **kwargs):
        self.language = self.index_page.locale.language_code
        return super().__call__(request, *args, **kwargs)

    def title(self):
        return f"{self.index_page.title} — УСВП Лубенської міської ради"

    def link(self):
        return self.index_page.url

    def description(self):
        return self.index_page.intro or self.index_page.title

    def items(self):
        return self.index_page.get_news()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        # Дата новини з форми редактора, а не момент першої публікації
        return timezone.make_aware(datetime.datetime.combine(item.date, datetime.time.min))
