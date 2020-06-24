from __future__ import unicode_literals

from django.contrib import auth
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, render
from django.views import generic

from courses.models import Membership
from storage.utils import parse_resource_id, serve_resource

from users.models import UserProfile
from users.profile.permissions import ProfilePermissionCalcer


class Access(object):
    def __init__(self, is_allowed):
        self.is_allowed = is_allowed
        self.show_profile_link = False

    @staticmethod
    def allow():
        return Access(True)

    @staticmethod
    def deny():
        return Access(False)

    def with_profile_link(self):
        self.show_profile_link = True
        return self


def _calc_access(request_user, target_user):
    if not request_user.is_authenticated:
        return Access.deny()

    if request_user.is_staff:
        return Access.allow().with_profile_link()
    if ProfilePermissionCalcer(request_user).calc(target_user.id) is not None:
        return Access.allow().with_profile_link()

    if request_user == target_user:
        return Access.allow()
    if target_user.is_staff:
        return Access.allow()

    def get_courses(user):
        return set(Membership.objects.filter(user=user).values_list('course_id', flat=True))

    if get_courses(request_user) & get_courses(target_user):
        return Access.allow()

    return Access.deny()


class UserCardView(generic.View):
    max_memberships = 10
    template_name = 'users/user_card.html'

    def get(self, request, user_id):
        user = get_object_or_404(auth.get_user_model(), pk=user_id)
        access = _calc_access(request.user, user)
        if not access.is_allowed:
            raise Http404('No access to the user')

        profile = user.userprofile
        course_memberships = Membership.objects.filter(user=user, role=Membership.STUDENT).\
            select_related('course', 'subgroup').\
            order_by('-id')[:self.max_memberships]

        context = {
            'user': user,
            'profile': profile,
            'show_profile_link': access.show_profile_link,
            'course_memberships': course_memberships,
        }
        return render(request, self.template_name, context)


class PhotoView(generic.View):
    def get(self, request, user_id, resource_id):
        resource_id = parse_resource_id(resource_id)
        valid_ids = UserProfile.objects.filter(user_id=user_id).values_list('photo', 'photo_thumbnail').first()
        if (valid_ids is not None) and (resource_id in valid_ids):
            return serve_resource(request, resource_id, content_type='image/jpeg', cache_forever=True)
        raise Http404('User or photo was not found.')
