import errno
import json
import os
import shutil

from pathlib import Path
from collections import namedtuple

from workerlib.iface import TestingReport

from .junitxml import parse_junitxml, extract_tests
from .buildjson import parse_buildjson, extract_compilation_log

JUNIT_XML = 'junit.xml'

SrcRelativePaths = namedtuple('SrcRelativePaths', ['checkerfile', 'testsdir', 'solutionfile'])
DstRelativePaths = namedtuple('DstRelativePaths', ['builddir', 'junitxmlfile'])


class BaseTester:
    def __init__(self, cache):
        self._cache = cache

    def run(self, job, sandbox_dir, callback):
        workdir = Path(sandbox_dir)
        self._cleanup(workdir)
        srcpaths = self._create_src_environment(job, workdir)
        dstpaths = self._declare_dst_environment()

        callback.set_compiling()
        self._build(job, workdir, srcpaths, dstpaths)
        buildjson = parse_buildjson(workdir / dstpaths.builddir / 'build.json')
        compiled, log = extract_compilation_log(buildjson)
        if not compiled:
            return TestingReport.compilation_error(log)

        callback.set_testing()
        self._execute(job, workdir, srcpaths, dstpaths)
        junitxml = parse_junitxml(workdir / dstpaths.junitxmlfile)
        return self._make_report(job, log, junitxml)

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
            checkerfile=self._write_checker(job, workdir),
            testsdir=self._write_tests(job, workdir),
            solutionfile=self._write_solution(job, workdir),
        )

    def _declare_dst_environment(self):
        return DstRelativePaths(
            builddir='build',
            junitxmlfile='junit.xml'
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
        checkerdir = self._create_dir(workdir, 'checker')
        for fn in ['conftest.py', 'build.py']:
            src = Path(__file__).parent / 'sandboxed' / fn
            shutil.copy(src, checkerdir / fn)

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

    def _make_build_command(self, job, srcdir, srcpaths, dstdir, dstpaths):
        cmd = [
            'python3', (srcdir / srcpaths.checkerfile).parent / 'build.py',
            srcdir / srcpaths.solutionfile,
            '--checker', srcdir / srcpaths.checkerfile,
            '--output-dir', dstdir / dstpaths.builddir,
        ]
        if job.solution_compiler:
            cmd.extend(['--compiler', job.solution_compiler])
        return [str(s) for s in cmd]

    def _make_execute_command(self, job, srcdir, srcpaths, dstdir, dstpaths):
        cmd = [
            'python3', '-m', 'pytest',
            srcdir / srcpaths.checkerfile,
            '--solution', srcdir / srcpaths.solutionfile,
            '--tests-dir', srcdir / srcpaths.testsdir,
            '--build-dir', srcdir / dstpaths.builddir,
            '--junitxml', dstdir / dstpaths.junitxmlfile,
            '--tb', 'short',
            '--timeout', str(job.default_time_limit / 1000),
            '-p', 'no:cacheprovider',
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
