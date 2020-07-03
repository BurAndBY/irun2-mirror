from collections import namedtuple

from django.contrib import messages
from django.utils.translation import ungettext

Diff = namedtuple('Diff', 'rows_added rows_removed')


def _perform(to_add, to_remove, model, keyname, extra_args):
    # first remove, then add (in order not to violate unique constraints)
    if to_remove:
        model.objects.filter(**{'{}__in'.format(keyname): to_remove}, **extra_args).delete()
    if to_add:
        objects = [model(**{keyname: pk}, **extra_args) for pk in to_add]
        model.objects.bulk_create(objects)
    return Diff(len(to_add), len(to_remove))


def _change_rowset(pks_before, pks_after, model, keyname, extra_args):
    before = set(pks_before)
    after = set(pks_after)

    to_add = after - before
    to_remove = before - after
    return _perform(to_add, to_remove, model, keyname, extra_args)


def _change_rowset_ordered(pks_before, pks_after, model, keyname, extra_args):
    equal_length = 0
    for i in range(min(len(pks_before), len(pks_after))):
        if pks_before[i] != pks_after[i]:
            break
        equal_length = i + 1

    to_add = pks_after[equal_length:]
    to_remove = pks_before[equal_length:]
    return _perform(to_add, to_remove, model, keyname, extra_args)


def change_rowset_3p(field_value, model, keyname, extra_args):
    return _change_rowset(field_value.initial_pks, field_value.pks, model, keyname, extra_args)


def change_rowset_ordered_3p(field_value, model, keyname, extra_args):
    return _change_rowset_ordered(field_value.initial_pks, field_value.pks, model, keyname, extra_args)


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
