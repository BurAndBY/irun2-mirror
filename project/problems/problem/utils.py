from django.contrib import messages
from django.utils import timezone
from django.utils.translation import ugettext

from problems.problem.validation import revalidate_testset


def register_new_test(test_case, problem, request):
    test_case.problem = problem
    test_case.ordinal_number = problem.testcase_set.count() + 1  # TODO: fix possible data race
    if request.user.is_authenticated():
        test_case.author_id = request.user.id
    test_case.creation_time = timezone.now()
    test_case.save()
    revalidate_testset(problem.id)

    msg = ugettext('Test %(no)d has been added.') % {'no': test_case.ordinal_number}
    messages.add_message(request, messages.INFO, msg)
