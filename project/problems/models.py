from django.db import models
from storage.storage import ResourceIdField
from mptt.models import MPTTModel, TreeForeignKey


class ProblemFolder(MPTTModel):
    name = models.CharField(max_length=50, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def __unicode__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']


class Problem(models.Model):
    number = models.IntegerField(blank=True, null=True, default=None)
    subnumber = models.IntegerField(blank=True, null=True, default=None)
    full_name = models.CharField(max_length=200, blank=True)
    short_name = models.CharField(max_length=32, blank=True)
    complexity = models.IntegerField(blank=True, null=True, default=None)
    offered = models.TextField(blank=True)  # public
    description = models.TextField(blank=True)  # public
    hint = models.TextField(blank=True)  # private

    input_filename = models.CharField(max_length=32, blank=True)
    output_filename = models.CharField(max_length=32, blank=True)

    folders = models.ManyToManyField(ProblemFolder)

    def _number(self):
        if self.number is None:
            return u''
        if self.subnumber is None:
            return u'{0}'.format(self.number)
        else:
            return u'{0}.{1}'.format(self.number, self.subnumber)

    def _numbered_name(self, name):
        if self.number:
            return u'{1}. {0}'.format(name, self._number())
        else:
            return u'{0}'.format(name)

    def numbered_full_name(self):
        return self._numbered_name(self.full_name)

    def numbered_short_name(self):
        return self._numbered_name(self.short_name)


class ProblemRelatedFile(models.Model):
    USER_FILE = 222
    GENERATOR = 218
    STATEMENT_HTML = 212
    STATEMENT_TEX = 211
    LIBRARY = 219
    CHECKER = 216
    SOLUTION_DESCRIPTION = 214
    AUTHORS_SOLUTION = 215

    FILE_TYPE_CHOICES = (
        (USER_FILE, 'User File'),
        (GENERATOR, 'Generator'),
        (STATEMENT_HTML, 'HTML Statement'),
        (STATEMENT_TEX, 'TeX Statement'),
        (LIBRARY, 'Library'),
        (CHECKER, 'Checker'),
        (SOLUTION_DESCRIPTION, 'Solution Description'),
        (AUTHORS_SOLUTION, 'Author\'s Solution'),
    )

    problem = models.ForeignKey(Problem)
    file_type = models.IntegerField(choices=FILE_TYPE_CHOICES, default=USER_FILE)
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    size = models.IntegerField()
    description = models.TextField()
    resource_id = ResourceIdField()


class TestCase(models.Model):
    problem = models.ForeignKey(Problem)
    ordinal_number = models.PositiveIntegerField(default=0)
    description = models.TextField()

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
        self.input_resource_id = resource_id
        self.input_size = f.size

    def set_answer(self, storage, f):
        resource_id = storage.save(f)
        self.answer_resource_id = resource_id
        self.answer_size = f.size
