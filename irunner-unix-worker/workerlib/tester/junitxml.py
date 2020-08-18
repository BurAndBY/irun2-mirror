import logging
import re
import xml.etree.ElementTree as ET

from workerlib.iface import (
    CheckFailed,
    Outcome,
    TestCaseResult,
)

PREFIXES = [
    '--------------------------------- Captured Out ---------------------------------\n',
    '--------------------------------- Captured Err ---------------------------------\n',
]


def parse_junitxml(path):
    try:
        return ET.parse(path)
    except (IOError, ET.ParseError):
        raise CheckFailed('Unable to parse JUnit XML')


def _do_extract_tests(job, test_suite, tests):
    for test_case in test_suite.findall('testcase'):
        if test_case.find('skipped') is not None:
            continue

        traceback = None
        outcome = Outcome.ACCEPTED

        if test_case.find('failure') is not None:
            outcome = Outcome.FAILED
            traceback = test_case.find('failure').text
            if traceback:
                tblines = traceback.splitlines()
                if len(tblines) > 0 and tblines[-1].startswith('E   Failed: Timeout >'):
                    outcome = Outcome.TIME_LIMIT_EXCEEDED

        if test_case.find('error') is not None:
            outcome = Outcome.CHECK_FAILED
            traceback = test_case.find('error').text

        test_name = test_case.attrib.get('name', '')
        if test_name == 'test_irunner_hidden':
            continue

        original_test = None
        m = re.search(r'\bcase#(?P<num>\d+)\b', test_name)
        if m is not None:
            idx = int(m.group('num')) - 1
            if 0 <= idx and idx < len(job.test_cases):
                original_test = job.test_cases[idx]

        time_ms = int(float(test_case.attrib['time']) * 1000)

        def _gettext(name):
            node = test_case.find(name)
            if node is not None:
                result = node.text
                for pref in PREFIXES:
                    if result.startswith(pref):
                        result = result[len(pref):]
                if result.endswith('\n\n') or result == '\n':
                    result = result[:-1]
                return result

        tests.append(TestCaseResult(
            original_test,
            outcome,
            None,
            None,
            time_ms,
            job.default_time_limit,
            test_name,
            traceback,
            _gettext('system-out'),
            _gettext('system-err')
        ))


def extract_tests(job, junitxml):
    root = junitxml.getroot()
    logging.info('JUnit XML: %s', ET.tostring(root, encoding='unicode'))

    tests = []
    if root.tag == 'testsuite':
        # the format depends on pytest version
        _do_extract_tests(job, root, tests)
    elif root.tag == 'testsuites':
        for test_suite in root.findall('testsuite'):
            _do_extract_tests(job, test_suite, tests)
    return tests
