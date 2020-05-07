from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.encoding import force_text

SIZE = 'size'
PAGE = 'page'


class IRunnerPaginationContext(object):
    def __init__(self):
        self.page_obj = None
        self.object_count = 0
        self.per_page_count = 0
        self.query_param_size = ''
        self.query_params_other = ''
        self.page_size_constants = []
        self.allow_all = False


class SimplePage(object):
    def __init__(self, object_list, size, number):
        self.object_list = object_list
        self.number = number
        self._size = size

    def has_previous(self):
        return self.number > 1

    def has_next(self):
        return True

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1

    def start_index(self):
        return self._size * (self.number - 1) + 1

    def end_index(self):
        return self._size * self.number


class IRunnerPaginator(object):
    def __init__(self, default_page_size, allow_all, show_total_count):
        self.default_page_size = default_page_size
        self.allow_all = allow_all
        self.page_size_constants = [7, 12, 25, 50, 100]
        self.show_total_count = show_total_count

    @staticmethod
    def _get_int_param(request, name, default=None, special={}):
        '''
        Gets non-negative integer from request GET-params.
        Returns None if no value is present.
        Throws Http404() on invalid values.
        May use predefined special values (i.e. string 'last' is mapped to the number of the last page).
        '''
        value = request.GET.get(name)
        if value is None:
            return default

        if value in special:
            return special[value]

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise Http404('{0} is not an integer'.format(name))

        if value < 0:
            raise Http404('{0} is negative'.format(name))

        return value

    def _validate_setup(self):
        '''
        Verifies that params set in __init__ are correct.
        Throws on error, returns nothing.
        '''
        assert self.default_page_size >= 0
        if self.default_page_size == 0:
            if not self.allow_all:
                raise ImproperlyConfigured('You must specify valid default page size if you do not allow to list all objects.')
        else:
            if self.default_page_size not in self.page_size_constants:
                raise ImproperlyConfigured('Default page size must occur in predefined page size choices.')

        if not all(x > 0 for x in self.page_size_constants):
            raise ImproperlyConfigured('All page size choices must be positive.')

    def _parse_page_size(self, request):
        '''
        Parses size param from query string and ensures it is valid.
        Always returns a non-negative integer.
        '''
        page_size = IRunnerPaginator._get_int_param(request, SIZE, default=self.default_page_size)
        if not self.allow_all:
            if (page_size == 0) or (page_size > max(self.page_size_constants)):
                raise Http404('Too large page requested')
        return page_size

    def _parse_page_number(self, request, special={}):
        return IRunnerPaginator._get_int_param(request, PAGE, default=1, special=special)

    def _list_page_sizes(self, size):
        '''
        Prepares ordered list of integers.
        '''
        s = set(self.page_size_constants)
        s.add(size)
        return sorted(filter(None, s))

    def _get_size_query_param(self, size):
        '''
        Returns '' or '&size=N' string.
        '''
        result = ''
        if size != self.default_page_size:
            # safe: no need to urlencode integers
            result = '&{0}={1}'.format(SIZE, size)
        return result

    def _get_other_query_params(self, request):
        '''
        Returns '' or '&key1=value1&key2=value2...' string made up with
        params that are not related to pagination.
        '''
        params = request.GET.copy()
        params.pop(SIZE, None)
        params.pop(PAGE, None)
        result = params.urlencode()
        if result:
            result = '&' + result
        return result

    def paginate(self, request, queryset):
        '''
        Returns a dict
        {
            'pagination_context': ...,
            'object_list': ...
        }
        '''

        self._validate_setup()

        page_size = self._parse_page_size(request)
        assert page_size >= 0

        pc = IRunnerPaginationContext()
        pc.per_page_count = page_size
        pc.page_size_constants = self._list_page_sizes(page_size)
        pc.query_param_size = self._get_size_query_param(page_size)
        pc.query_params_other = self._get_other_query_params(request)
        pc.allow_all = self.allow_all

        if page_size == 0:
            # no pagination
            actual_queryset = queryset

            # create fake paginator to get total object list
            paginator = Paginator(queryset, 1)

            pc.object_count = paginator.count
            pc.page_obj = None

        elif not self.show_total_count:
            # fast pagination: don't know the total object and page count
            page_number = self._parse_page_number(request)

            bottom = (page_number - 1) * page_size
            top = bottom + page_size
            actual_queryset = queryset[bottom:top]

            pc.object_count = None
            pc.page_obj = SimplePage(actual_queryset, page_size, page_number)

        else:
            paginator = Paginator(queryset, page_size, orphans=0, allow_empty_first_page=True)
            page_number = self._parse_page_number(request, special={'last': paginator.num_pages})
            page = None
            try:
                page = paginator.page(page_number)
            except InvalidPage as e:
                raise Http404('Invalid page (%(page_number)s): %(message)s' % {
                    'page_number': page_number,
                    'message': force_text(e)
                })
            actual_queryset = page.object_list

            pc.object_count = paginator.count
            pc.page_obj = page

        return {
            'pagination_context': pc,
            'object_list': actual_queryset
        }
