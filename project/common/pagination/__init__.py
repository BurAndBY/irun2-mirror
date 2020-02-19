from .utils import IRunnerPaginator


def paginate(request, queryset, default_page_size=0, allow_all=True):
    p = IRunnerPaginator(default_page_size, allow_all)
    return p.paginate(request, queryset)
