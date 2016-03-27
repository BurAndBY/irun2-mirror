# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from common.outcome import Outcome
from proglangs.models import Compiler
from storage.models import FileMetadataBase
from storage.storage import ResourceIdField


class ProblemFolder(MPTTModel):
    name = models.CharField(max_length=64)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def __unicode__(self):
        return self.name


class Problem(models.Model):
    number = models.IntegerField(_('number'), blank=True, null=True, default=None)
    subnumber = models.IntegerField(_('subnumber'), blank=True, null=True, default=None)
    full_name = models.CharField(_('full name'), max_length=200, blank=True)
    short_name = models.CharField(_('short name'), max_length=32, blank=True)
    difficulty = models.IntegerField(_('difficulty'), blank=True, null=True, default=None)

    input_filename = models.CharField(_('input file name'), max_length=32, blank=True)
    output_filename = models.CharField(_('output file name'), max_length=32, blank=True)

    folders = models.ManyToManyField(ProblemFolder, verbose_name=_('folders'))

    class Meta:
        ordering = ['number', 'subnumber', 'full_name']

    def get_formatted_number(self):
        if self.number is None:
            return u''
        if self.subnumber is None:
            return u'{0}'.format(self.number)
        else:
            return u'{0}.{1}'.format(self.number, self.subnumber)

    def _numbered_name(self, name):
        if self.number is not None:
            if name:
                return u'{0}. {1}'.format(self.get_formatted_number(), name)
            else:
                return self.get_formatted_number()
        else:
            return name

    def numbered_full_name(self):
        return self._numbered_name(self.full_name)

    def numbered_full_name_difficulty(self):
        result = self.numbered_full_name()
        if self.difficulty is not None:
            return u'[{0}] {1}'.format(self.difficulty, result)
        else:
            return result

    def numbered_short_name(self):
        return self._numbered_name(self.short_name)


class ProblemExtraInfo(models.Model):
    problem = models.OneToOneField(Problem, null=False, on_delete=models.CASCADE, primary_key=True)
    description = models.TextField(_('description'), blank=True)  # public
    hint = models.TextField(_('hint'), blank=True)  # private


class ProblemRelatedFile(FileMetadataBase):
    STATEMENT_TEX = 211
    STATEMENT_HTML = 212
    ADDITIONAL_STATEMENT_FILE = 213
    SOLUTION_DESCRIPTION = 214
    SAMPLE_INPUT_FILE = 220
    SAMPLE_OUTPUT_FILE = 221
    USER_FILE = 222

    FILE_TYPE_CHOICES = (
        (STATEMENT_TEX, _('TeX statement')),
        (STATEMENT_HTML, _('HTML statement')),
        (ADDITIONAL_STATEMENT_FILE, _('Additional statement file')),
        (SOLUTION_DESCRIPTION, _('Solution description')),
        (SAMPLE_INPUT_FILE, _('Sample input file')),
        (SAMPLE_OUTPUT_FILE, _('Sample output file')),
        (USER_FILE, _('User file')),
    )

    TEST_CASE_IMAGE_FILE_TYPES = (
        ADDITIONAL_STATEMENT_FILE,
        SAMPLE_INPUT_FILE,
        SAMPLE_OUTPUT_FILE,
        USER_FILE,
    )
    TEX_FILE_TYPES = (
        STATEMENT_TEX,
    )

    problem = models.ForeignKey(Problem)
    file_type = models.IntegerField(_('file type'), choices=FILE_TYPE_CHOICES)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        unique_together = ('problem', 'filename')


class ProblemRelatedSourceFile(FileMetadataBase):
    AUTHORS_SOLUTION = 215
    CHECKER = 216
    CONTESTANT_SOLUTION = 217
    GENERATOR = 218
    LIBRARY = 219
    VALIDATOR = 223

    FILE_TYPE_CHOICES = (
        (AUTHORS_SOLUTION, _('Author\'s solution')),
        (CHECKER, _('Checker')),
        (CONTESTANT_SOLUTION, _('Contestant solution')),
        (GENERATOR, _('Generator')),
        (LIBRARY, _('Library')),
        (VALIDATOR, _('Validator')),
    )

    # null for global checkers
    problem = models.ForeignKey(Problem, null=True)
    file_type = models.IntegerField(_('file type'), choices=FILE_TYPE_CHOICES)
    description = models.TextField(_('description'), blank=True)
    compiler = models.ForeignKey(Compiler, verbose_name=_('compiler'))

    class Meta:
        unique_together = ('problem', 'filename')


class TestCase(models.Model):
    problem = models.ForeignKey(Problem)
    ordinal_number = models.PositiveIntegerField(_('number'), default=0)
    description = models.TextField(_('description'), blank=True)

    input_resource_id = ResourceIdField()
    input_size = models.IntegerField(default=0)

    answer_resource_id = ResourceIdField()
    answer_size = models.IntegerField(default=0)

    time_limit = models.IntegerField()
    memory_limit = models.IntegerField(default=0)
    points = models.IntegerField(default=1)

    class Meta:
        unique_together = ('problem', 'ordinal_number')

    def set_input(self, storage, f):
        resource_id = storage.save(f)
        updated = (self.input_resource_id != resource_id)
        self.input_resource_id = resource_id
        self.input_size = f.size
        return updated

    def set_answer(self, storage, f):
        resource_id = storage.save(f)
        updated = (self.answer_resource_id != resource_id)
        self.answer_resource_id = resource_id
        self.answer_size = f.size
        return updated


class Validation(models.Model):
    problem = models.OneToOneField(Problem)
    is_pending = models.BooleanField(default=False)
    validator = models.ForeignKey(ProblemRelatedSourceFile, null=True, blank=True, on_delete=models.SET_NULL)
    general_failure_reason = models.CharField(max_length=64, blank=True)


class TestCaseValidation(models.Model):
    validation = models.ForeignKey(Validation)
    input_resource_id = ResourceIdField()
    is_valid = models.BooleanField()
    validator_message = models.CharField(max_length=255, blank=True)
