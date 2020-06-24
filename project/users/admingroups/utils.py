from users.models import AdminGroup


def user_belongs_to_group(user, group_id):
    '''
    Makes a single simple query.
    '''
    return AdminGroup.users.through.objects.\
        filter(user_id=user.id, admingroup=group_id).\
        exists()
