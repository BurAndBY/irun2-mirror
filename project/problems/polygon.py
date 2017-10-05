import zipfile
import xml.etree.ElementTree as ET

from django.core.files.base import ContentFile
from django.utils import timezone

from problems.models import Problem, ProblemExtraInfo, TestCase, ProblemRelatedFile, ProblemRelatedSourceFile
from storage.storage import create_storage
from storage.utils import store_and_fill_metadata

HIDE_HEADER_CSS = '.problem-statement .header { display: none; }'


def get_full_name(root, language):
    for name in root.findall('names/name'):
        if name.attrib['language'] == language:
            return name.attrib['value']
    return u''


def parse_input_output_file(name):
    if name in (None, 'stdin', 'stdout'):
        return u''
    return name


def get_int(elem, name):
    return int(elem.find(name).text)


def load_source_file(myzip, elem, problem, file_type, compiler):
    path = elem.find('source').attrib['path']
    fd = ContentFile(myzip.read(path), name=path.split('/')[-1])

    related_file = ProblemRelatedSourceFile(problem=problem, file_type=file_type, compiler=compiler)
    store_and_fill_metadata(fd, related_file)
    related_file.full_clean()
    related_file.save()


def load_statement(myzip, problem, language):
    prefix = 'statements/.html/{0}/'.format(language)
    for path in myzip.namelist():
        if path.startswith(prefix):
            filename = path[len(prefix):]
            if not filename:
                # skip the directory itself
                continue

            file_type = ProblemRelatedFile.STATEMENT_HTML if (filename == 'problem.html') else ProblemRelatedFile.ADDITIONAL_STATEMENT_FILE
            related_file = ProblemRelatedFile(problem=problem, file_type=file_type)

            data = myzip.read(path)
            # HACK
            if filename == 'problem-statement.css':
                data += HIDE_HEADER_CSS

            fd = ContentFile(data, name=filename)
            store_and_fill_metadata(fd, related_file)
            related_file.full_clean()
            related_file.save()


def parse_archive(myzip, language, compiler, user):
    problem_xml_data = myzip.read('problem.xml')
    root = ET.fromstring(problem_xml_data)

    problem = Problem()
    problem.short_name = root.attrib['short-name']
    problem.full_name = get_full_name(root, language)

    judging = root.find('judging')
    problem.input_filename = parse_input_output_file(judging.get('input-file'))
    problem.output_filename = parse_input_output_file(judging.get('output-file'))
    problem.full_clean()
    problem.save()

    tests = []
    storage = create_storage()

    ts = timezone.now()

    tl_ml_set = False
    total_tests = 0

    extra_info = ProblemExtraInfo(problem=problem)

    for testset in judging.findall('testset'):
        time_limit = get_int(testset, 'time-limit')
        memory_limit = get_int(testset, 'memory-limit')

        if not tl_ml_set:
            extra_info.default_time_limit = time_limit
            extra_info.default_memory_limit = memory_limit
            tl_ml_set = True

        test_count = get_int(testset, 'test-count')

        input_pattern = testset.find('input-path-pattern').text
        answer_pattern = testset.find('answer-path-pattern').text
        number = 0

        for i, test in enumerate(testset.findall('tests/test')):
            number = i + 1
            total_tests += 1

            if test.get('sample') == 'true':
                if extra_info.sample_test_count + 1 == total_tests:
                    extra_info.sample_test_count += 1

            tc = TestCase(problem=problem, ordinal_number=total_tests, time_limit=time_limit, memory_limit=memory_limit)
            tc.set_input(storage, ContentFile(myzip.read(input_pattern % (number,))))
            tc.set_answer(storage, ContentFile(myzip.read(answer_pattern % (number,))))
            tc.author = user
            tc.creation_time = ts
            tc.full_clean()
            tests.append(tc)

        if number != test_count:
            raise ValueError('"test-count" is {}, number of <test> tags is {}'.format(test_count, number))

    extra_info.save()

    TestCase.objects.bulk_create(tests)

    if compiler is not None:
        for checker in root.findall('assets/checker'):
            load_source_file(myzip, checker, problem, ProblemRelatedSourceFile.CHECKER, compiler)

        for validator in root.findall('assets/validators/validator'):
            load_source_file(myzip, validator, problem, ProblemRelatedSourceFile.VALIDATOR, compiler)

    load_statement(myzip, problem, language)

    return problem


def import_full_package(upload, language, compiler, user, folder_id=None):
    with zipfile.ZipFile(upload, 'r', allowZip64=True) as myzip:
        problem = parse_archive(myzip, language, compiler, user)
    if folder_id is not None:
        problem.folders.add(folder_id)
