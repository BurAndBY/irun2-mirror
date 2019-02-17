from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from home.registry import (
    HomePageBlock,
    HomePageBlockStyle,
    HomePageBlockFactory,
)

from contests.models import Contest, UnauthorizedAccessLevel

NUM_CONTESTS = 3


class ContestBlockFactory(HomePageBlockFactory):
    template = 'contests/homeblock.html'
    icon = 'stats'

    def create_blocks(self, request):
        if request.user.is_authenticated():
            my_contests = Contest.objects.filter(membership__user=request.user).distinct()
            my_contest_count = my_contests.count()
            if my_contest_count > 0:
                yield HomePageBlock(
                    style=HomePageBlockStyle.MY,
                    icon=self.icon,
                    name=_('My contests'),
                    count=my_contest_count,
                    content=render_to_string(self.template, {
                        'contests': my_contests.order_by('-start_time')[:NUM_CONTESTS],
                        'view_all_url': reverse('contests:my')
                    })
                )

        public_contests = Contest.objects.exclude(unauthorized_access=UnauthorizedAccessLevel.NO_ACCESS)
        public_contests = public_contests.order_by('-start_time')[:NUM_CONTESTS]
        if public_contests:
            yield HomePageBlock(
                style=HomePageBlockStyle.COMMON,
                icon=self.icon,
                name=_('Contest results'),
                count=None,
                content=render_to_string(self.template, {
                    'contests': public_contests,
                    'view_all_url': reverse('contests:index')
                })
            )
