from django.conf import settings


def system_name(request):
    return {
        'system_full_name': 'Insight Runner 2',
        'system_short_name': 'iRunner 2',
        'external_links': settings.EXTERNAL_LINKS,
    }
