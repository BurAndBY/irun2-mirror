from django.db import models
from storage.storage import ResourceIdField


class Problem(models.Model):
    number = models.CharField(max_length=8)
    full_name = models.CharField(max_length=200, blank=True)
    short_name = models.CharField(max_length=32, blank=True)
    complexity = models.IntegerField(null=True)
    offered = models.TextField()  # public
    description = models.TextField()  # public
    hint = models.TextField()  # private

    input_filename = models.CharField(max_length=32, blank=True)
    output_filename = models.CharField(max_length=32, blank=True)

    def _numbered_name(self, name):
        if self.number:
            return u'{1}. {0}'.format(name, self.number)
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

    input_file = ResourceIdField()
    input_size = models.IntegerField(default=0)

    answer_file = ResourceIdField()
    answer_size = models.IntegerField(default=0)

    time_limit = models.IntegerField()
    memory_limit = models.IntegerField(null=True)
    points = models.IntegerField(default=1)

    class Meta:
        unique_together = ('problem', 'ordinal_number')

    def set_input(self, storage, f):
        resource_id = storage.save(f)
        self.input_file = resource_id
        self.input_size = f.size

    def set_answer(self, storage, f):
        resource_id = storage.save(f)
        self.answer_file = resource_id
        self.answer_size = f.size
