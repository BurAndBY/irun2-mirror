from __future__ import unicode_literals

from django.contrib import auth
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, render
from django.views import generic

from courses.models import Membership
from storage.utils import parse_resource_id, serve_resource

from users.models import UserProfile
from users.profile.permissions import ProfilePermissionCalcer


def is_allowed(request_user, target_user):
    if not request_user.is_authenticated:
        return False
    if request_user == target_user:
        return True
    if request_user.is_staff or target_user.is_staff:
        return True

    if ProfilePermissionCalcer(request_user).calc(target_user.id) is not None:
        return True

    def get_courses(user):
        return set(Membership.objects.filter(user=user).values_list('course_id', flat=True))

    if get_courses(request_user) & get_courses(target_user):
        return True

    return False


class UserCardView(generic.View):
    max_memberships = 10
    template_name = 'users/user_card.html'

    def get(self, request, user_id):
        user = get_object_or_404(auth.get_user_model(), pk=user_id)
        if not is_allowed(request.user, user):
            return HttpResponseForbidden()
        profile = user.userprofile
        course_memberships = Membership.objects.filter(user=user, role=Membership.STUDENT).\
            select_related('course', 'subgroup').\
            order_by('-id')[:self.max_memberships]

        context = {
            'user': user,
            'profile': profile,
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
