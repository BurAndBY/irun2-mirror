from pygments.styles import get_all_styles

DEFAULT = 'default'


def list_highlight_styles():
    return sorted(get_all_styles())


def get_highlight_style(request):
    style = request.session.get('highlight_style', DEFAULT)
    if style not in get_all_styles():
        style = DEFAULT
    return style


def update_highlight_style(request):
    new_style = request.GET.get('style')
    if new_style is not None:
        if new_style in get_all_styles():
            request.session['highlight_style'] = new_style
