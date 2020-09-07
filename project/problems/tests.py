from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory

from common.tree.fields import FOLDER_ID_PLACEHOLDER
from cauth.acl.accessmode import AccessMode
from users.models import AdminGroup

from problems.description import IDescriptionImageLoader, render_description
from problems.models import Problem, ProblemAccess, ProblemFolder, ProblemFolderAccess
from problems.fields import ThreePanelGenericProblemMultipleChoiceField
from problems.problem.permissions import ProblemPermissionCalcer


class SimpleDescriptionImageLoader(IDescriptionImageLoader):
    def __init__(self, images):
        self._images = images

    def get_image_list(self):
        return self._images


class DescriptionTests(TestCase):
    def test_simple(self):
        loader = SimpleDescriptionImageLoader(['1.png'])
        r = render_description(
            'Look at the <image>: ${image:1.png}. Text following & the image.',
            loader
        )

        self.assertEqual(r.text, 'Look at the <image>: . Text following & the image.')
        self.assertEqual(r.images, ['1.png'])

    def test_404(self):
        loader = SimpleDescriptionImageLoader([])
        r = render_description(r'${image:404.png}', loader)
        self.assertEqual(r.text, '')
        self.assertEqual(r.images, [])


class FakeForm(forms.Form):
    problems = ThreePanelGenericProblemMultipleChoiceField(required=True)


class ProblemFoldersTests(TestCase):
    def test_parentfolders(self):
        # Fill the data
        algo = ProblemFolder.objects.create(name='Algorithms')
        graphs = ProblemFolder.objects.create(name='Graphs', parent=algo)
        dp = ProblemFolder.objects.create(name='DP', parent=algo)
        removed = ProblemFolder.objects.create(name='Removed', parent=dp)

        contests = ProblemFolder.objects.create(name='Contests')
        year_2019 = ProblemFolder.objects.create(name='2019', parent=contests)
        year_2020 = ProblemFolder.objects.create(name='2020', parent=contests)

        bfs = Problem.objects.create(full_name='Breadth-first search', short_name='BFS', number=1)
        bfs.folders.add(graphs)
        dfs = Problem.objects.create(full_name='Depth-first search', short_name='DFS', number=2)
        dfs.folders.add(graphs)
        dijkstra = Problem.objects.create(full_name='Dijkstra', number=10)
        dijkstra.folders.add(graphs)
        dijkstra.folders.add(year_2019)
        fake = Problem.objects.create(full_name='FAKE')
        fake.folders.add(removed)
        new = Problem.objects.create(full_name='Secret problem', short_name='Secret', number=42)
        new.folders.add(year_2020)
        new2 = Problem.objects.create(full_name='Non-secret problem', short_name='Non-secret', number=42)
        new2.folders.add(year_2020)
        orphan = Problem.objects.create(full_name='Orphan problem')  # in the root dir

        # Test
        self.assertEqual(Problem.objects.count(), 7)
        self.assertEqual(ProblemFolder.objects.count(), 7)
        self.assertEqual(graphs.problem_set.count(), 3)
        self.assertEqual(removed.problem_set.count(), 1)
        self.assertEqual(contests.problem_set.count(), 0)
        self.assertEqual(Problem.objects.filter(folders__name='Algorithms').count(), 0)
        self.assertEqual(Problem.objects.filter(folders__name='Graphs').count(), 3)
        self.assertEqual(Problem.objects.filter(folders__name='DP').count(), 0)
        self.assertEqual(dijkstra.folders.count(), 2)

        user = get_user_model().objects.create_user(username='eps')
        admin = get_user_model().objects.create_user(username='root', is_staff=True)
        admingroup = AdminGroup.objects.create(name='TA')
        admingroup.users.add(user)

        ProblemFolderAccess.objects.create(folder=algo, group=admingroup, mode=AccessMode.MODIFY)
        ProblemAccess.objects.create(problem=new2, user=user, mode=AccessMode.READ)

        # Test ProblemPermissionCalcer
        access = ProblemPermissionCalcer(user).calc_in_bulk([bfs.id, new.id, new2.id])
        self.assertTrue(access.get(bfs.id).can_edit)
        self.assertIsNone(access.get(new.id))
        self.assertIsNotNone(access.get(new2.id))
        self.assertFalse(access.get(new2.id).can_edit)
        access = ProblemPermissionCalcer(admin).calc_in_bulk([bfs.id, new.id, new2.id])
        self.assertTrue(access.get(bfs.id).can_edit)
        self.assertTrue(access.get(new.id).can_edit)
        self.assertTrue(access.get(new2.id).can_edit)

        rf = RequestFactory()

        def run(me, params, initial=None):
            request = rf.post('/', params)
            form = FakeForm(request.POST, initial=initial)
            form.fields['problems'].configure(
                url_template='/aba/caba/{}'.format(FOLDER_ID_PLACEHOLDER),
                user=me,
                initial=initial
            )
            return form

        f = run(user, {})
        self.assertFalse(f.is_valid())

        f = run(user, {'problems': bfs.id})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['problems'].pks, [bfs.id])

        f = run(user, {'problems': 100500})
        self.assertFalse(f.is_valid())

        f = run(admin, {'problems': 100500})
        self.assertFalse(f.is_valid())

        f = run(user, {'problems': 'abacaba'})
        self.assertFalse(f.is_valid())

        f = run(user, {'problems': [dfs.id, bfs.id]})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['problems'].pks, [dfs.id, bfs.id])

        f = run(user, {'problems': [dfs.id, fake.id, bfs.id]})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['problems'].pks, [dfs.id, fake.id, bfs.id])

        f = run(user, {'problems': orphan.id})
        self.assertFalse(f.is_valid())

        f = run(user, {'problems': orphan.id}, initial=Problem.objects.all())
        self.assertTrue(f.is_valid())

        f = run(admin, {'problems': orphan.id})
        self.assertTrue(f.is_valid())
