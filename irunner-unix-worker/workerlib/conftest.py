import pytest
import json
import pathlib


def pytest_addoption(parser):
    parser.addoption('--solution', action='store', help='path to solution file')
    parser.addoption('--tests-dir', action='store', help='path to directory with tests')


@pytest.fixture
def solution(request):
    '''
    Path to solution file
    '''
    return request.config.getoption('--solution')


class TestCaseFile:
    def __init__(self, path):
        self.path = path

    def json(self):
        with self.path.open() as fd:
            return json.load(fd)

    def text(self):
        with self.path.open() as fd:
            lines = fd.read().splitlines()
        return ''.join('{}\n'.format(line) for line in lines)


class TestCase:
    def __init__(self):
        self.input = None
        self.answer = None


def _load_test_cases(metafunc):
    test_cases = []

    tests_dir = metafunc.config.getoption('tests_dir')
    if tests_dir is not None:
        tests_dir = pathlib.Path(tests_dir)
        with (tests_dir / 'list.json').open() as fd:
            jsontests = json.load(fd)

        for jsontest in jsontests:
            tc = TestCase()
            file = jsontest.get('inputFile')
            if file is not None:
                tc.input = TestCaseFile(tests_dir / file)
            file = jsontest.get('answerFile')
            if file is not None:
                tc.answer = TestCaseFile(tests_dir / file)
            test_cases.append(tc)

    return test_cases


def pytest_generate_tests(metafunc):
    if 'testcase' in metafunc.fixturenames:
        test_cases = _load_test_cases(metafunc)
        ids = ['case#{}'.format(i + 1) for i in range(len(test_cases))]
        metafunc.parametrize('testcase', test_cases, ids=ids)
