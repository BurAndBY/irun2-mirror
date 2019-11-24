import io
import shutil
import pathlib
import tarfile
import logging

import docker

from .tester import BaseTester


def _get_file_data(container, srcpath, dstpath):
    tarstream = io.BytesIO()
    import docker
    try:
        strm, stat = container.get_archive(srcpath)
    except docker.errors.NotFound:
        return
    for chunk in strm:
        tarstream.write(chunk)
    tarstream.seek(0)

    with tarfile.TarFile(fileobj=tarstream, mode='r') as tar:
        file = tar.extractfile(srcpath.name)
        with dstpath.open('wb') as outfile:
            shutil.copyfileobj(file, outfile)


class DockerTester(BaseTester):
    def __init__(self, sandbox_dir, cache):
        super().__init__(sandbox_dir, cache)
        self._client = docker.from_env()

    def _execute(self, job, workdir, srcpaths, dstpaths):
        rodir = pathlib.PosixPath('/opt/irunner/src')
        rwdir = pathlib.PosixPath('/opt/irunner/dst')

        cmd = self._make_command(job, rodir, srcpaths, rwdir, dstpaths)
        c = self._client.containers.create(
            'irunner-worker',
            command=cmd,
            environment=self._make_env({}),
            cap_add=['SYS_PTRACE'],
            volumes={
                str(workdir.resolve()): {'bind': str(rodir), 'mode': 'ro'}
            }
        )
        c.start()
        c.wait()
        logging.info('Logs: %s', c.logs())
        _get_file_data(c, rwdir / dstpaths.junitxmlfile, workdir / dstpaths.junitxmlfile)
        c.remove()
