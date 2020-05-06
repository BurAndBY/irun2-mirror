from django import forms
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.http import Http404
from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

from .widgets import TwoPanelSelectMultiple, ThreePanelSelectMultiple, Choice
from .inmemory import Tree
from .key import folder_id_or_404


FOLDER_ID_PLACEHOLDER = '__FOLDER_ID__'


class TwoPanelModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    '''
    TODO: It is slow because it loads all model instances. It can be done better.
    '''
    def __init__(self, model, folder_model, url_pattern, url_params=(), queryset=None, clean_to_list=False, *args, **kwargs):
        if queryset is None:
            queryset = model.objects.all()

        widget = TwoPanelSelectMultiple(folder_model, url_pattern, url_params)
        self.model = model
        self.folder_model = folder_model
        self.clean_to_list = clean_to_list

        super(TwoPanelModelMultipleChoiceField, self).__init__(queryset=queryset, widget=widget, *args, **kwargs)

    @classmethod
    def ajax(cls, object_list):
        data = [{'id': obj.pk, 'name': cls.label_from_instance(obj)} for obj in object_list]
        return JsonResponse({'data': data}, json_dumps_params={'ensure_ascii': False})

    def clean(self, value):
        qs = super(TwoPanelModelMultipleChoiceField, self).clean(value)
        if self.clean_to_list:
            mp = {force_text(obj.pk): obj for obj in qs.order_by()}
            return [mp[pk] for pk in value]
        else:
            return qs


class Value(object):
    def __init__(self):
        self.valid = True
        self.pks = []
        self.initial_pks = []
        self.choices = []

    def is_valid(self):
        return self.valid


class ThreePanelModelMultipleChoiceField(forms.Field):
    '''
    In order to use the form field, you need to:
      * inherit from this class, create your own Field class and define `root_name`, `model`, ... at class scope;
      * override `label_from_instance()`, `build_pk2folders()`, `load_folder()`;
      * use your Field class in a Form;
      * after constructing the Form, call `configure()`.
    '''

    # override this settings in your class
    root_name = None
    model = object
    folder_model = object
    folder_access_model = object

    @classmethod
    def label_from_instance(cls, obj):
        # Override it to customize the label.
        return str(obj)

    @classmethod
    def build_pk2folders(cls, pks):
        raise NotImplementedError()

    @classmethod
    def load_folder(cls, folder_id):
        raise NotImplementedError()

    # Implementation
    widget = ThreePanelSelectMultiple
    default_error_messages = {
        'invalid_value': _('Got an invalid value.')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inmemory_tree = None

    def configure(self, initial, user, url_template):
        self.initial = initial
        self.widget.url_template = url_template
        self._inmemory_tree = self.widget.inmemory_tree = self._load_tree(user)

    @classmethod
    def _load_tree(cls, user):
        return Tree.load(cls.root_name, cls.folder_model, cls.folder_access_model, user)

    @classmethod
    def ajax(cls, user, folder_id_or_root):
        folder_id = folder_id_or_404(folder_id_or_root)
        # TODO: may be slow, optimize?
        # We actually need a single folder here, not the whole tree.
        inmemory_tree = cls._load_tree(user)
        try:
            node = inmemory_tree.find(folder_id)
        except KeyError:
            raise Http404('folder not found or no access')
        response = {'name': node.name}
        if node.access:  # if no access, only folder name is given, without children
            response['items'] = [{
                'id': obj.pk,
                'name': cls.label_from_instance(obj)
            } for obj in cls.load_folder(folder_id)]

        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})

    def _extract_pks(self, value, label_cache):
        if value is None:
            return
        for v in value:
            if isinstance(v, self.model):
                label_cache.setdefault(v.pk, self.label_from_instance(v))
                yield v.pk
            elif isinstance(v, int):
                yield v
            elif isinstance(v, str):
                yield int(v)
            else:
                raise AssertionError('Unable to get pk from {}'.format(type(v).__name__))

    def prepare_value(self, value):
        if self._inmemory_tree is None:
            raise ImproperlyConfigured('the {} form field was not properly configured'.format(self.name))

        result = Value()
        label_cache = {}
        result.initial_pks = list(self._extract_pks(self.initial, label_cache))
        initial_pks_set = set(result.initial_pks)

        try:
            pks = list(self._extract_pks(value, label_cache))
        except (TypeError, ValueError):
            # rare case of malicious input (non-integer pks are supplied in a form)
            result.valid = False
            return result

        pk2folders = self.build_pk2folders(pks)
        tmp = []
        pks_missing_labels = []  # collect pks for which we still do not know a label
        for pk in pks:
            access = 0
            folder_names = []
            for folder_id in pk2folders.get(pk, []):
                try:
                    node = self._inmemory_tree.find(folder_id)
                except KeyError:  # probably no access
                    continue
                folder_names.append(node.name)
                access = max(access, node.access)

            if (access == 0) and not (pk in initial_pks_set):
                # the form contains an instance which is missing or forbidden
                result.valid = False
                continue
            # not able to generate Choice here because a label may be not known
            tmp.append((pk, folder_names))
            result.pks.append(pk)
            if pk not in label_cache:
                pks_missing_labels.append(pk)

        if pks_missing_labels:
            # fetch complete objects for fillng the labels that are missing
            for pk, v in self.model.objects.in_bulk(pks_missing_labels).items():
                label_cache.setdefault(pk, self.label_from_instance(v))

        for pk, folder_names in tmp:
            result.choices.append(Choice(pk, label_cache.get(pk, ''), folder_names))
        return result

    def to_python(self, value):
        # Don't know where it is used...
        raise NotImplementedError()

    def clean(self, value):
        value = self.prepare_value(value)
        assert isinstance(value, Value)
        if self.required and not value.pks:
            raise ValidationError(self.error_messages['required'], code='required')
        if not value.is_valid():
            raise ValidationError(self.error_messages['invalid_value'], code='invalid_value')
        self.run_validators(value)
        return value
