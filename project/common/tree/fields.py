from django import forms
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.http import Http404
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from cauth.acl.accessmode import AccessMode

from .widgets import ThreePanelSelectMultiple, Choice
from .key import folder_id_or_404


FOLDER_ID_PLACEHOLDER = '__FOLDER_ID__'


class Value(object):
    def __init__(self):
        self.valid = True
        self.pks = []
        self.initial_pks = []
        self.choices = []

    def is_valid(self):
        return self.valid

    def __iter__(self):
        for pk in self.pks:
            yield pk


class ThreePanelModelMultipleChoiceField(forms.Field):
    '''
    In order to use the form field, you need to:
      * inherit from this class, create your own Field class and define `loader_cls` at class scope;
      * override `label_from_instance()`, `build_pk2folders()`;
      * use your Field class in a Form;
      * after constructing the Form, call `configure()`.
    '''

    # override this settings in your class
    loader_cls = object

    @classmethod
    def label_from_instance(cls, obj):
        # Override it to customize the label.
        return str(obj)

    @classmethod
    def build_pk2folders(cls, pks):
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
        self._inmemory_tree = self.widget.inmemory_tree = self.loader_cls.load_tree(user)
        self._extra_pks_set = set(self.loader_cls.get_extra_objects(user).values_list('pk', flat=True))

    @classmethod
    def ajax(cls, user, folder_id_or_root):
        folder_id = folder_id_or_404(folder_id_or_root)
        # TODO: may be slow, optimize?
        # We actually need a single folder here, not the whole tree.
        inmemory_tree = cls.loader_cls.load_tree(user)
        try:
            node = inmemory_tree.find(folder_id)
        except KeyError:
            raise Http404('folder not found or no access')
        response = {
            'name': node.name,
            'items': [{
                'id': obj.pk,
                'name': cls.label_from_instance(obj)
            } for obj in cls.loader_cls.get_folder_content(user, node)]
        }
        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})

    def _extract_pks(self, value, label_cache):
        if value is None:
            return
        for v in value:
            if isinstance(v, self.loader_cls.model):
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

            if (access == 0) and (pk not in initial_pks_set) and (pk not in self._extra_pks_set):
                # the form contains an instance which is missing or forbidden
                result.valid = False
                continue
            # not able to generate Choice here because a label may be not known
            tmp.append((pk, folder_names))

        self._populate_label_cache(label_cache, (pk for pk, _ in tmp))
        for pk, folder_names in tmp:
            result.pks.append(pk)
            result.choices.append(Choice(pk, label_cache.get(pk, '<#{}>'.format(pk)), folder_names))
        return result

    def _populate_label_cache(self, label_cache, pks):
        # collect pks for which we still do not know a label
        pks_missing_labels = [pk for pk in pks if pk not in label_cache]
        if pks_missing_labels:
            # fetch complete objects for fillng the labels that are missing
            for pk, v in self.loader_cls.model.objects.in_bulk(pks_missing_labels).items():
                label_cache.setdefault(pk, self.label_from_instance(v))

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


class FolderChoiceField(forms.ChoiceField):
    default_error_messages = {
        'read_only_folder': _('You do not have permission to add entries to this folder.'),
        'not_readable_folder': _('You do not have permission to list entries of this folder.'),
    }

    def __init__(self, *args, **kwargs):
        self._loader_cls = kwargs.pop('loader_cls')
        self._required_mode = kwargs.pop('required_mode', AccessMode.MODIFY)
        self._none_means_not_set = kwargs.pop('none_means_not_set', False)
        self._user = None
        self._inmemory_tree = None
        super().__init__(*args, **kwargs)

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value
        self._inmemory_tree = self._loader_cls.load_tree(self._user)

        if self._none_means_not_set:
            not_set_label = '[{}]'.format(_('Not set'))
            choices = [(None, not_set_label)] + self._inmemory_tree.as_choices(show_root=False)
        else:
            choices = self._inmemory_tree.as_choices(show_root=True)

        self.choices = choices

    def _get_pk(self, value):
        if value in self.empty_values:
            return None
        return int(value)

    def clean(self, value):
        value = super().clean(value)
        pk = self._get_pk(value)

        if self._none_means_not_set:
            if pk is None:
                return None

        try:
            node = self._inmemory_tree.find(pk)
        except (TypeError, KeyError, ValueError):
            raise ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )

        if self._required_mode == AccessMode.MODIFY:
            if node.access != AccessMode.MODIFY:
                raise ValidationError(
                    self.error_messages['read_only_folder'],
                    code='read_only_folder',
                )
        if self._required_mode == AccessMode.READ:
            if node.access == 0:
                raise ValidationError(
                    self.error_messages['not_readable_folder'],
                    code='not_readable_folder',
                )
        return node.instance
