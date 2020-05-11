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

DEFAULT = 'default'

BuildResult = namedtuple('BuildResult', 'success exe_name log')


class IBuilder:
    def get_available_configurations(self):
        yield DEFAULT

    def build(self, source, configuration, target_dir):
        raise NotImplementedError()


class BaseScriptPatcher(IBuilder):
    interpreter = None

    def _format_shebang(self):
        return '#!/usr/bin/env {}\n'.format(self.interpreter)

    def _copy_add_shebang(self, source, destination):
        with source.open('rU') as infile:
            with destination.open('w', newline='\n') as outfile:
                outfile.write(self._format_shebang())
                first = True
                for line in infile:
                    if first:
                        first = False
                        if line.startswith('#!'):
                            continue
                    outfile.write(line)

    def build(self, source, configuration, target_dir):
        exe_name = source.name
        destination = target_dir / exe_name
        self._copy_add_shebang(source, destination)
        destination.chmod(0o755)
        return BuildResult(True, exe_name, None)


class BashScriptPatcher(BaseScriptPatcher):
    interpreter = 'bash'


class PythonScriptPatcher(BaseScriptPatcher):
    interpreter = 'python'


class GccCompiler(IBuilder):
    args = {
        'O0': ['-O0'],
        'O2': ['-O2'],
        'asan': ['-fsanitize=address'],
        'ubsan': ['-fsanitize=undefined'],
        'tsan': ['-fsanitize=thread'],
    }
    default_configuration = 'O2'

    def _exe_name(self, configuration):
        if configuration == DEFAULT:
            return 'program'
        return 'program_{}'.format(configuration.lower())

    def _get_cmd(self, configuration, source_name, exe_name):
        if configuration not in self.args:
            configuration = self.default_configuration

        cmd = ['gcc', '-o', exe_name, '-fno-omit-frame-pointer', '-g', '-Wall', '-Wextra', '-pthread', source_name]
        cmd.extend(self.args[configuration])
        return cmd

    def get_available_configurations(self):
        for configuration in self.args:
            yield configuration

    def build(self, source, configuration, target_dir):
        source_name = source.name
        exe_name = self._exe_name(configuration)

        with TemporaryDirectory(dir=target_dir) as tmp:
            shutil.copy(source, tmp)
            cmd = self._get_cmd(configuration, source_name, exe_name)
            p = subprocess.Popen(cmd, cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            log, _ = p.communicate()
            if p.returncode == 0:
                (Path(tmp) / exe_name).rename(target_dir / exe_name)
                return BuildResult(True, exe_name, log)
        return BuildResult(False, None, log)


def _get_builder_class(compiler, extension):
    compiler_rules = [
        (r'^GNUC($|\d)', GccCompiler),
        (r'^GCC($|\d)', GccCompiler),
        (r'^SHELL$', BashScriptPatcher),
        (r'^PYTHON', PythonScriptPatcher),
    ]
    extension_rules = {
        '.c': GccCompiler,
        '.sh': BashScriptPatcher,
    }

    if compiler:
        for regex, kls in compiler_rules:
            if re.match(regex, compiler):
                return kls
    return extension_rules.get(extension)


def run(source, compiler, configurations, output_dir):
    builder_class = _get_builder_class(compiler, source.suffix)
    builder = builder_class()
    available = set(builder.get_available_configurations())

    results = []

    def run(cfg):
        res = builder.build(source, cfg, output_dir)
        results.append({
            'configuration': cfg,
            'success': res.success,
            'file': res.exe_name,
            'log': res.log,
        })
        return res.success

    success = True
    built = False
    if configurations:  # need to build anything
        for cfg in configurations:
            if cfg in available:
                success &= run(cfg)
                built = True
            if not success:
                break
        if not built:
            success &= run(DEFAULT)

    return {'success': success, 'results': results}


def _extract_configurations_from_checker(path):
    spec = importlib.util.spec_from_file_location('checker', path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    return getattr(checker, 'BUILD_CONFIGURATIONS', [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='path to source file')
    parser.add_argument('--checker', help='path to checker')
    parser.add_argument('--compiler', help='compiler ID')
    parser.add_argument('--output-dir', help='output directory', default=os.curdir)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    configurations = []
    if args.checker:
        configurations = _extract_configurations_from_checker(args.checker)

    result = run(Path(args.source), args.compiler, configurations, output_dir)

    with (output_dir / 'build.json').open('w') as fd:
        json.dump(result, fd)


if __name__ == '__main__':
    main()
