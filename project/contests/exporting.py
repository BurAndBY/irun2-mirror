import xml.dom.minidom
import xml.etree.ElementTree as ET

from django.utils.encoding import smart_text
from django.utils import timezone

from common.outcome import Outcome
from solutions.models import Solution, Judgement
from proglangs.models import Compiler

from contests.services import SolutionKind
from contests.services import total_minutes, total_seconds


def export_to_s4ris_json(contest, results):
    runs = [{
        'contestant': run.user.get_full_name(),
        'problemLetter': run.labeled_problem.letter,
        'timeMinutesFromStart': total_minutes(run.when),
        'success': (run.kind is SolutionKind.ACCEPTED),
    } for run in results.all_runs if run.kind in (SolutionKind.ACCEPTED, SolutionKind.REJECTED)]

    json = {
        'contestName': smart_text(contest),
        'problemLetters': [lp.letter for lp in results.contest_descr.labeled_problems],
        'contestants': [ur.user.get_full_name() for ur in results.user_results],
        'runs': runs
    }
    if contest.freeze_time is not None:
        json['freezeTimeMinutesFromStart'] = total_minutes(contest.freeze_time)
    return json


EJUDGE_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'


def as_ejudge_ts(ts):
    return timezone.localtime(ts).strftime(EJUDGE_DATETIME_FORMAT)


EJUDGE_OUTCOME_CODES = {
    Outcome.ACCEPTED: 'OK',
    Outcome.COMPILATION_ERROR: 'CE',
    Outcome.WRONG_ANSWER: 'WA',
    Outcome.TIME_LIMIT_EXCEEDED: 'TL',
    Outcome.MEMORY_LIMIT_EXCEEDED: 'ML',
    Outcome.IDLENESS_LIMIT_EXCEEDED: 'IL',
    Outcome.RUNTIME_ERROR: 'RT',
    Outcome.PRESENTATION_ERROR: 'PE',
    Outcome.SECURITY_VIOLATION: 'SV',
    Outcome.CHECK_FAILED: 'CF'
}


def export_to_ejudge_xml(contest, results):
    root = ET.Element('runlog')

    root.attrib['contest_id'] = smart_text(contest.id)
    root.attrib['duration'] = smart_text(total_seconds(contest.duration))
    root.attrib['sched_start_time'] = root.attrib['start_time'] = as_ejudge_ts(contest.start_time)
    root.attrib['stop_time'] = as_ejudge_ts(contest.start_time + contest.duration)
    root.attrib['current_time'] = as_ejudge_ts(timezone.now())
    if contest.freeze_time is not None:
        root.attrib['fog_time'] = smart_text(total_seconds(contest.duration - contest.freeze_time))

    ET.SubElement(root, 'name').text = smart_text(contest)

    users = ET.SubElement(root, 'users')
    for ur in results.user_results:
        elem = ET.SubElement(users, 'user')
        elem.attrib['id'] = smart_text(ur.user.id)
        elem.attrib['name'] = ur.user.get_full_name()

    problems = ET.SubElement(root, 'problems')
    for lp in results.contest_descr.labeled_problems:
        elem = ET.SubElement(problems, 'problem')
        elem.attrib['id'] = smart_text(lp.problem.id)
        elem.attrib['short_name'] = smart_text(lp.letter)
        elem.attrib['long_name'] = smart_text(lp.problem.full_name)

    languages = ET.SubElement(root, 'languages')
    runs = ET.SubElement(root, 'runs')

    solutions = Solution.objects.select_related('best_judgement').filter(contestsolution__contest=contest).in_bulk()
    compiler_ids = set()

    for run in results.all_runs:
        if run.kind not in (SolutionKind.ACCEPTED, SolutionKind.REJECTED):
            continue
        solution = solutions.get(run.solution_id)
        if solution is None:
            # something strage
            continue

        elem = ET.SubElement(runs, 'run')

        elem.attrib['run_id'] = smart_text(run.solution_id)
        elem.attrib['time'] = smart_text(total_seconds(run.when))

        bj = solution.best_judgement
        if (bj is not None) and (bj.status == Judgement.DONE):
            elem.attrib['status'] = EJUDGE_OUTCOME_CODES.get(bj.outcome, '')
            if bj.test_number != 0:
                elem.attrib['test'] = smart_text(bj.test_number)

        elem.attrib['user_id'] = smart_text(solution.author_id)
        elem.attrib['prob_id'] = smart_text(solution.problem_id)
        elem.attrib['lang_id'] = smart_text(solution.compiler_id)
        elem.attrib['nsec'] = smart_text(0)
        compiler_ids.add(solution.compiler_id)

    for compiler in Compiler.objects.filter(pk__in=compiler_ids):
        elem = ET.SubElement(languages, 'language')
        elem.attrib['id'] = smart_text(compiler.id)
        elem.attrib['short_name'] = compiler.handle
        elem.attrib['long_name'] = compiler.description

    xml_data = ET.tostring(root, 'utf-8')
    reparsed = xml.dom.minidom.parseString(xml_data)
    return reparsed.toprettyxml()
