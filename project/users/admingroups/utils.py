from users.models import AdminGroup


def user_belongs_to_group(user, group_id):
    '''
    Makes a single simple query.
    '''
    return AdminGroup.users.through.objects.\
        filter(user_id=user.id, admingroup=group_id).\
        exists()


def filter_admingroups(qs, user, field='group'):
    admingroup_ids = getattr(user, 'admingroup_ids', None)
    if admingroup_ids is not None:
        # Cool, we have a precached list of groups of the user
        return qs.filter(**{'{}_id__in'.format(field): admingroup_ids})
    else:
        # Need to perform a JOIN
        return qs.filter(**{'{}__users'.format(field): user})
