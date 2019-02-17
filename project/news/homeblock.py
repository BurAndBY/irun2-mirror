from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from home.registry import (
    HomePageBlock,
    HomePageBlockStyle,
    HomePageBlockFactory,
)

from news.models import NewsMessage


class NewsBlockFactory(HomePageBlockFactory):
    template = 'news/homeblock.html'

    def create_blocks(self, request):
        news = NewsMessage.objects.filter(is_public=True).order_by('-when')
        if news:
            yield HomePageBlock(
                style=HomePageBlockStyle.COMMON,
                icon='bullhorn',
                name=_('News'),
                count=len(news),
                content=render_to_string(self.template, {'news': news})
            )
