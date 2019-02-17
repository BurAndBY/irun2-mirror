# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from contests.homeblock import ContestBlockFactory
from courses.homeblock import CourseBlockFactory
from news.homeblock import NewsBlockFactory

from home.registry import HomePageBlockStyle

NUM_CONTESTS = 3

HOME_PAGE_BLOCK_FACTORIES = [
    CourseBlockFactory(),
    ContestBlockFactory(),
    NewsBlockFactory(),
]


def home(request):
    blocks = []
    for factory in HOME_PAGE_BLOCK_FACTORIES:
        blocks.extend(factory.create_blocks(request))

    context = {
        'common_blocks': [block for block in blocks if block.style == HomePageBlockStyle.COMMON],
        'my_blocks': [block for block in blocks if block.style == HomePageBlockStyle.MY],
    }
    return render(request, 'home/home.html', context)


def about(request):
    return render(request, 'home/about.html', {})


def language(request):
    next = request.GET.get('next')
    return render(request, 'home/language.html', {'redirect_to': next})


def error403(request):
    return render(request, 'home/error403.html', {}, status=403)
