from .utils import IRunnerPaginator


def paginate(request, queryset, default_page_size=0, allow_all=True, show_total_count=True):
    p = IRunnerPaginator(default_page_size, allow_all, show_total_count)
    return p.paginate(request, queryset)
