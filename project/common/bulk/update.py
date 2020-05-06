from collections import namedtuple

from django.contrib import messages
from django.utils.translation import ungettext

Diff = namedtuple('Diff', 'rows_added rows_removed')


def _change_rowset(pks_before, pks_after, model, keyname, extra_args):
    before = set(pks_before)
    after = set(pks_after)

    to_add = after - before
    if to_add:
        objects = [model(**{keyname: pk}, **extra_args) for pk in to_add]
        model.objects.bulk_create(objects)

    to_remove = before - after
    if to_remove:
        model.objects.filter(**{'{}__in'.format(keyname): to_remove}).delete()

    return Diff(len(to_add), len(to_remove))


def change_rowset_3p(field_value, model, keyname, extra_args):
    return _change_rowset(field_value.initial_pks, field_value.pks, model, keyname, extra_args)


def notify_users_changed(request, diff):
    msgs = []
    if diff.rows_added > 0:
        msg = ungettext(
            '%(count)d user was added.',
            '%(count)d users were added.',
            diff.rows_added) % {
            'count': diff.rows_added,
            }
        msgs.append(msg)
    if diff.rows_removed > 0:
        msg = ungettext(
            '%(count)d user was removed.',
            '%(count)d users were removed.',
            diff.rows_removed) % {
            'count': diff.rows_removed,
            }
        msgs.append(msg)
    if msgs:
        messages.add_message(request, messages.INFO, ' '.join(msgs))
