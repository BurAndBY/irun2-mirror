from django.http import Http404

from common.tree.key import folder_id_or_404
from common.tree.inmemory import Tree


class FolderMixin(object):
    loader_cls = object
    needs_real_folder = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inmemory_tree'] = self.inmemory_tree
        context['folder'] = self.node
        context['folder_id'] = self.node.id
        return context

    @staticmethod
    def _parse_folder_id(value, needs_real_folder):
        fid = folder_id_or_404(value)
        if fid is None and needs_real_folder:
            raise Http404('operation may not be applied to the root folder')
        return fid

    @staticmethod
    def _find_node(tree, folder_id):
        try:
            return tree.find(folder_id)
        except KeyError:
            raise Http404('the folder does not exist or access is denied')

    def dispatch(self, request, *args, **kwargs):
        folder_id = self._parse_folder_id(kwargs.pop('folder_id_or_root'), self.needs_real_folder)
        self.inmemory_tree = self.loader_cls.load_tree(request.user)
        self.node = self._find_node(self.inmemory_tree, folder_id)
        return super().dispatch(request, *args, **kwargs)
