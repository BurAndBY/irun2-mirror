# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import os
import zipfile

from django.core.management.base import BaseCommand

from problems.models import ProblemRelatedFile
from problems.texrenderer import render_tex
from storage.storage import create_storage

MAX_SIZE = 10 * 1024 * 1024  # bytes

CSS_FILE_NAME = 'irunner2.css'
TEX_FILE_NAME = 'statement.tex'
HTML_FILE_NAME = 'statement.html'
LOG_FILE_NAME = 'tex2html.log'

logger = logging.getLogger('irunner_import')

TEMPLATE = '''\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" type="text/css" href="../irunner2.css">
        <title>Problem {problem_id}</title>
    </head>
    <body>
        <div class="ir-problem-statement">{content}</div>
    </body>
</html>
'''


class Command(BaseCommand):
    help = 'Dumps TeX statements and their HTML versions'

    def add_arguments(self, parser):
        parser.add_argument('archive', help='zip archive to create')

    def handle(self, *args, **options):
        archive = options['archive']
        logger.info('Output file: %s', archive)

        storage = create_storage()

        with zipfile.ZipFile(archive, 'w') as zf:
            self._run(storage, zf)

    def _run(self, storage, zf):
        css = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'irunner2.css')
        zf.write(css, CSS_FILE_NAME)

        problem_ids = set()
        for tex_file in ProblemRelatedFile.objects.filter(file_type=ProblemRelatedFile.STATEMENT_TEX):
            if tex_file.problem_id in problem_ids:
                logger.warning('Multiple statements for problem %d', tex_file.problem_id)
                continue
            problem_ids.add(tex_file.problem_id)
            self._write_problem(storage, zf, tex_file)

    def _write_problem(self, storage, zf, tex_file):
        problem_id = tex_file.problem_id
        logger.debug('Processing problem %d', problem_id)

        tex_data = storage.represent(tex_file.resource_id)
        if tex_data is None:
            logger.error('Problem %d: no TeX statement resource found', problem_id)
        if tex_data.complete_text is None:
            logger.error('Problem %d: TeX statement could not be decoded', problem_id)

        tex_text = self._normalize_newlines(tex_data.complete_text)
        zf.writestr('{}/{}'.format(problem_id, TEX_FILE_NAME), tex_text.encode('utf-8'))

        self._save_tex2html(zf, problem_id, tex_text)
        self._save_aux(zf, storage, problem_id)

    def _save_tex2html(self, zf, problem_id, tex_text):
        render_result = render_tex(tex_text, 'input.txt', 'output.txt')
        zf.writestr('{}/{}'.format(problem_id, LOG_FILE_NAME), render_result.log.encode('utf-8'))
        zf.writestr('{}/{}'.format(problem_id, HTML_FILE_NAME), self._make_page(problem_id, render_result.output).encode('utf-8'))

    def _save_aux(self, zf, storage, problem_id):
        for aux_file in ProblemRelatedFile.objects.filter(problem_id=problem_id, file_type=ProblemRelatedFile.ADDITIONAL_STATEMENT_FILE):
            if not self._is_good_aux_file(aux_file):
                continue
            blob, is_complete = storage.read_blob(aux_file.resource_id, max_size=MAX_SIZE)
            if not is_complete:
                logger.error('Problem %d: file %s is too large', problem_id, aux_file.filename)
                continue
            zf.writestr('{}/{}'.format(problem_id, aux_file.filename), blob)

    def _make_page(self, problem_id, content):
        return TEMPLATE.format(problem_id=problem_id, content=content)

    def _is_good_aux_file(self, aux_file):
        fn = aux_file.filename.lower()
        for suffix in ('.png', '.jpg', '.gif', '.bmp'):
            if fn.endswith(suffix):
                return True

    def _normalize_newlines(self, s):
        return ''.join((line + '\n') for line in s.splitlines())
