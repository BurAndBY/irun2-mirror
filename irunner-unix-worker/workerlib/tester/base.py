import errno
import json
import os
import shutil

from pathlib import Path
from collections import namedtuple

from workerlib.iface import TestingJob, TestingReport

from .junitxml import parse_junitxml, extract_tests
from .buildjson import parse_buildjson, extract_compilation_log

JUNIT_XML = 'junit.xml'
BUILD_PY = 'build.py'
TEST_PY = 'test.py'

SrcRelativePaths = namedtuple('SrcRelativePaths', ['checkerdir', 'testsdir', 'solutionfile'])
DstRelativePaths = namedtuple('DstRelativePaths', ['builddir', 'junitxmlfile', 'reportfile'])


class BaseTester:
    def __init__(self, cache):
        self._cache = cache

    def run(self, job, sandbox_dir, callback):
        workdir = Path(sandbox_dir)
        self._cleanup(workdir)
        srcpaths = self._create_src_environment(job, workdir)
        dstpaths = self._declare_dst_environment(job)

        callback.set_compiling()
        self._build(job, workdir, srcpaths, dstpaths)
        buildjson = parse_buildjson(workdir / dstpaths.builddir / 'build.json')
        compiled, compilation_log = extract_compilation_log(buildjson)
        if not compiled:
            return TestingReport.compilation_error(compilation_log)

        callback.set_testing()
        self._execute(job, workdir, srcpaths, dstpaths)

        if dstpaths.reportfile is not None:
            return TestingReport.from_json(job, compilation_log, workdir / dstpaths.reportfile)
        else:
            assert dstpaths.junitxmlfile is not None
            junitxml = parse_junitxml(workdir / dstpaths.junitxmlfile)
            return self._make_report(job, compilation_log, junitxml)

    @staticmethod
    def _cleanup(workdir):
        try:
            shutil.rmtree(workdir)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        workdir.mkdir()

    def _create_src_environment(self, job, workdir):
        return SrcRelativePaths(
            checkerdir=self._write_checker(job, workdir),
            testsdir=self._write_tests(job, workdir),
            solutionfile=self._write_solution(job, workdir),
        )

    def _declare_dst_environment(self, job):
        if job.checker_kind == TestingJob.PYTEST:
            return DstRelativePaths(
                builddir='build',
                junitxmlfile='junit.xml',
                reportfile=None
            )
        else:
            return DstRelativePaths(
                builddir='build',
                junitxmlfile=None,
                reportfile='report.json'
            )

    @staticmethod
    def _create_dir(workdir, name):
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
        checker_dir = self._create_dir(workdir, 'checker')
        scripts_src_dir = Path(__file__).parent / 'sandboxed'

        for lib in job.libraries:
            shutil.copy(self._cache[lib.resource_id], checker_dir / lib.filename)

        if job.checker_kind == TestingJob.PYTEST:
            shutil.copy(scripts_src_dir / 'build-pytest.py', checker_dir / BUILD_PY)
            shutil.copy(scripts_src_dir / 'conftest.py', checker_dir / 'conftest.py')
            shutil.copy(scripts_src_dir / 'pytest.ini', checker_dir / 'pytest.ini')
            shutil.copy(self._cache[job.checker_resource_id], checker_dir / TEST_PY)
        else:
            shutil.copy(scripts_src_dir / 'build-custom.py', checker_dir / BUILD_PY)
            shutil.copy(self._cache[job.checker_resource_id], checker_dir / 'package.zip')

        return 'checker'

    @staticmethod
    def _is_binary(filename):
        for ext in ['.zip', '.tar', '.tar.gz', '.tgz']:
            if filename.endswith(ext):
                return True
        return False

    @staticmethod
    def _copy_converting_newlines(src, dst):
        if BaseTester._is_binary(dst.name):
            shutil.copyfile(src, dst)
            return
        with src.open('rU') as infile:
            with dst.open('w', newline='\n') as outfile:
                for line in infile:
                    outfile.write(line)

    def _write_solution(self, job, workdir):
        solutiondir = self._create_dir(workdir, 'solution')
        # shutil.copy(self._cache[job.solution_resource_id], solutiondir / job.solution_filename)
        self._copy_converting_newlines(self._cache[job.solution_resource_id], solutiondir / job.solution_filename)
        return os.path.join('solution', job.solution_filename)

    def _make_build_command(self, job, srcdir, srcpaths, dstdir, dstpaths):
        checkerdir = srcdir / srcpaths.checkerdir
        cmd = ['python3', checkerdir / BUILD_PY,
               srcdir / srcpaths.solutionfile,
               '--output-dir', dstdir / dstpaths.builddir]

        if job.checker_kind == TestingJob.PYTEST:
            cmd.extend(['--checker', checkerdir / TEST_PY])
        else:
            cmd.extend(['--tests', checkerdir / 'package.zip'])
            cmd.extend(['--build-script', checkerdir / 'build.sh'])

        if job.solution_compiler:
            cmd.extend(['--compiler', job.solution_compiler])

        return [str(s) for s in cmd]

    def _make_execute_command(self, job, srcdir, srcpaths, dstdir, dstpaths):
        if job.checker_kind == TestingJob.PYTEST:
            cmd = [
                'python3', '-m', 'pytest',
                srcdir / srcpaths.checkerdir / TEST_PY,
                '--solution', srcdir / srcpaths.solutionfile,
                '--tests-dir', srcdir / srcpaths.testsdir,
                '--build-dir', dstdir / dstpaths.builddir,
                '--junitxml', dstdir / dstpaths.junitxmlfile,
                '--tb', 'short',
                '--timeout', str(job.default_time_limit / 1000),
                '-p', 'no:cacheprovider',
            ]
        else:
            cmd = [
                'python3', dstdir / dstpaths.builddir / 'runner.py',
                '--build-dir', dstdir / dstpaths.builddir,
                '--irunner-report-json', dstdir / dstpaths.reportfile,
            ]

        return [str(s) for s in cmd]

    def _make_env(self, env):
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        return env

    def _make_report(self, job, log, junitxml):
        '''
        Receives parsed junitxml, returns TestingReport
        '''
        tests = extract_tests(job, junitxml)
        return TestingReport.from_tests(tests, log)

    def _build(self, job, workdir, srcpaths, dstpaths):
        '''
        Implementation should create in workdir
        files and directories specified in dstpaths.
        '''
        raise NotImplementedError()

    def _execute(self, job, workdir, srcpaths, dstpaths):
        '''
        Implementation should create in workdir
        files and directories specified in dstpaths.
        '''
        raise NotImplementedError()
