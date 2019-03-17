import os
import re
import json
import errno
import shutil
import logging
import pathlib
import tempfile
import subprocess
import xml.etree.ElementTree as ET

from collections import namedtuple

from .iface import (
    Outcome,
    TestCaseResult,
    TestingReport,
)

JUNIT_XML = 'junit.xml'

SrcRelativePaths = namedtuple('SrcRelativePaths', ['checkerfile', 'testsdir', 'solutionfile'])
DstRelativePaths = namedtuple('DstRelativePaths', ['junitxmlfile'])


class BaseTester:
    def __init__(self, sandbox_dir, cache):
        self._sandbox_dir = pathlib.Path(sandbox_dir)
        self._cache = cache

    def run(self, job):
        self._cleanup()
        self._sandbox_dir.mkdir()
        workdir = self._sandbox_dir
        srcpaths = self._create_src_environment(job, workdir)
        dstpaths = self._declare_dst_environment()

        self._execute(job, workdir, srcpaths, dstpaths)

        try:
            junitxml = ET.parse(workdir / dstpaths.junitxmlfile)
        except (IOError, ET.ParseError):
            logging.exception('Unable to parse JUnit XML')
            return TestingReport.check_failed()
        return self._make_report(job, junitxml)

    def _cleanup(self):
        try:
            shutil.rmtree(self._sandbox_dir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def _create_src_environment(self, job, workdir):
        return SrcRelativePaths(
            checkerfile=self._write_checker(job, workdir),
            testsdir=self._write_tests(job, workdir),
            solutionfile=self._write_solution(job, workdir),
        )

    def _declare_dst_environment(self):
        return DstRelativePaths(junitxmlfile='junit.xml')

    def _create_dir(self, workdir, name):
        d = workdir / name
        d.mkdir()
        return d

    def _write_tests(self, job, workdir):
        testsdir = self._create_dir(workdir, 'tests')
        mapper = {}

        test_resource_ids = set()
        for test in job.test_cases:
            if test.input_resource_id is not None:
                test_resource_ids.add(test.input_resource_id)
            if test.answer_resource_id is not None:
                test_resource_ids.add(test.answer_resource_id)

        test_filenames = set()
        for resource_id in test_resource_ids:
            cached_path = self._cache[resource_id]

            filename = cached_path.name
            assert filename not in test_filenames
            test_filenames.add(filename)
            mapper[resource_id] = filename

            temp_path = testsdir / filename
            shutil.copy(cached_path, temp_path)

        with (testsdir / 'list.json').open('w') as fd:
            json.dump(self._create_test_list_json(job, mapper), fd)
        return 'tests'

    @staticmethod
    def _create_test_list_json(job, mapper):
        ts = []
        for t in job.test_cases:
            tt = {}
            if t.input_resource_id is not None:
                tt['inputFile'] = mapper[t.input_resource_id]
            if t.answer_resource_id is not None:
                tt['answerFile'] = mapper[t.answer_resource_id]
            ts.append(tt)
        return ts

    def _write_checker(self, job, workdir):
        checkerdir = self._create_dir(workdir, 'checker')
        conftest = pathlib.Path(__file__).parent / 'conftest.py'
        shutil.copy(conftest, checkerdir / 'conftest.py')
        checkerfile = checkerdir / 'test.py'
        shutil.copy(self._cache[job.checker_resource_id], checkerfile)
        return os.path.join('checker', 'test.py')

    @staticmethod
    def _copy_converting_newlines(src, dst):
        with src.open('rU') as infile:
            with dst.open('w', newline='\n') as outfile:
                for line in infile:
                    outfile.write(line)

    def _write_solution(self, job, workdir):
        solutiondir = self._create_dir(workdir, 'solution')
        # shutil.copy(self._cache[job.solution_resource_id], solutiondir / job.solution_filename)
        self._copy_converting_newlines(self._cache[job.solution_resource_id], solutiondir / job.solution_filename)
        return os.path.join('solution', job.solution_filename)

    def _make_command(self, job, srcdir, srcpaths, dstdir, dstpaths):
        cmd = [
            'python3', '-m', 'pytest',
            srcdir / srcpaths.checkerfile,
            '--solution', srcdir / srcpaths.solutionfile,
            '--tests-dir', srcdir / srcpaths.testsdir,
            '--junitxml', dstdir / dstpaths.junitxmlfile,
            '--tb', 'short',
            '--timeout', str(job.default_time_limit * 0.001),
            '-p', 'no:cacheprovider',
        ]
        return [str(s) for s in cmd]

    def _make_env(self, env):
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return env

    def _make_report(self, job, junitxml):
        '''
        Receives parsed junitxml, returns TestingReport
        '''
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
            if test_case.find('error') is not None:
                outcome = Outcome.CHECK_FAILED
                traceback = test_case.find('error').text

            test_name = test_case.attrib.get('name', '')

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
        return TestingReport.from_tests(tests)

    def _execute(self, job, workdir, srcpaths, dstpaths):
        '''
        Implementation should create in workdir
        files and directories specified in dstpaths.
        '''
        raise NotImplementedError()


class LocalTester(BaseTester):
    def _execute(self, job, workdir, srcpaths, dstpaths):
        absworkdir = workdir.resolve()
        cmd = self._make_command(job, absworkdir, srcpaths, absworkdir, dstpaths)

        with tempfile.TemporaryDirectory() as tempdir:
            logging.info(cmd)
            p = subprocess.Popen(cmd, cwd=tempdir, env=self._make_env(os.environ.copy()))
            p.wait()
