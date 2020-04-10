from contests.models import Contest
from courses.models import Course
from problems.models import ProblemRelatedSourceFile
from solutions.models import Solution
from users.models import UserProfile


def replace_compiler(old, new):
    for contest in Contest.objects.filter(compilers__id=old):
        contest.compilers.add(new)
        contest.compilers.remove(old)

    for course in Course.objects.filter(compilers__id=old):
        course.compilers.add(new)
        course.compilers.remove(old)

    ProblemRelatedSourceFile.objects.filter(compiler_id=old).update(compiler_id=new)
    Solution.objects.filter(compiler_id=old).update(compiler_id=new)
    UserProfile.objects.filter(last_used_compiler=old).update(last_used_compiler=new)
