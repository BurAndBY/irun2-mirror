import logging
import os
import subprocess
import tempfile

from .base import BaseTester


class LocalTester(BaseTester):
    def _run_locally(self, cmd):
        with tempfile.TemporaryDirectory() as tempdir:
            logging.info(cmd)
            p = subprocess.Popen(cmd, cwd=tempdir, env=self._make_env(os.environ.copy()))
            p.wait()

    def _build(self, job, workdir, srcpaths, dstpaths):
        absworkdir = workdir.resolve()
        cmd = self._make_build_command(job, absworkdir, srcpaths, absworkdir, dstpaths)
        self._run_locally(cmd)

    def _execute(self, job, workdir, srcpaths, dstpaths):
        absworkdir = workdir.resolve()
        cmd = self._make_execute_command(job, absworkdir, srcpaths, absworkdir, dstpaths)
        self._run_locally(cmd)
