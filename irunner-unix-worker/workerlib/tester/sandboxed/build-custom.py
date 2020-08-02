import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess

from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory

BuildResult = namedtuple('BuildResult', 'success exe_name log')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='path to source file (.cpp or .zip)')
    parser.add_argument('--compiler', help='compiler selected by participant')
    parser.add_argument('--tests', help='path to tests package (zip-archive)',
                        default=os.path.join(os.curdir, 'package.zip'))
    parser.add_argument('--build_script', help='user-defined build logic',
                        default=os.path.join(os.curdir, 'build.sh'))
    parser.add_argument('--output-dir', help='output directory',
                        default=os.curdir)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(dir=output_dir) as tmp:
        cmd = [args.build_script, args.source, args.tests, tmp, args.output_dir]
        if args.compiler:
            cmd.append(args.compiler)

        p = subprocess.Popen(cmd, cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True)
        log, _ = p.communicate()
        success = (p.returncode == 0)

        log = log.replace(tmp, '')
        log = log.replace(args.source, '')
        log = log.replace(args.tests, '')
        log = log.replace(args.build_script, '')
        log = log.replace(args.output_dir, '')

    result = {
        'success': success,
        'results': [{
            'configuration': 'custom',
            'success': success,
            'file': str(output_dir),
            'log': log,
        }],
    }
    with (output_dir / 'build.json').open('w') as fd:
        json.dump(result, fd)


if __name__ == '__main__':
    main()
