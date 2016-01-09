import views


def paginate(request, queryset, defualt_page_size=None):
    '''
    Returns a dict
    {
        'pagination_context': ...,
        'object_list': ...
    }

    TODO: Implement IRunnerBaseListView through this function.
    '''
    view = views.IRunnerBaseListView()
    view.request = request
    view.paginate_by = defualt_page_size
    view.object_list = queryset
    view.kwargs = {}
    data = view.get_context_data()

    return {
        'pagination_context': data['pagination_context'],
        'object_list': data['object_list']
    }
