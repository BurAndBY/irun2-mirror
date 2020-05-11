import logging
import re
import xml.etree.ElementTree as ET

from workerlib.iface import (
    CheckFailed,
    Outcome,
    TestCaseResult,
)


def parse_junitxml(path):
    try:
        return ET.parse(path)
    except (IOError, ET.ParseError):
        logging.exception('Unable to parse JUnit XML')
        raise CheckFailed()


def extract_tests(job, junitxml):
    tests = []
    test_suite = junitxml.getroot()
    logging.info('JUnit XML: %s', ET.tostring(test_suite, encoding='unicode'))

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
                return node.text

        tests.append(TestCaseResult(
            original_test,
            outcome,
            time_ms,
            job.default_time_limit,
            test_name,
            traceback,
            _gettext('system-out'),
            _gettext('system-err')
        ))
    return tests
