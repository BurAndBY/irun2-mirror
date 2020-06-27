from cauth.acl.accessmode import AccessMode
from users.admingroups.utils import filter_admingroups
from common.tree.inmemory import Tree


def _enforce_acl(node, acl, mode):
    node.access = max(mode, acl.get(node.id, -1))

    children_left = []
    mode_to_push = node.access if node.access > 0 else -1
    for child in node.children:
        if _enforce_acl(child, acl, mode_to_push):
            children_left.append(child)
    node.children = children_left

    if node.children:
        _make_node_visible(node)
    return node.access >= 0


def _sort_levels(node):
    node.children.sort(key=lambda child: child.name)
    for child in node.children:
        _sort_levels(child)


def _make_node_visible(node):
    node.access = max(node.access, 0)


class FolderLoader(object):
    root_name = None
    model = object
    folder_model = object
    folder_access_model = object

    @classmethod
    def load_tree(cls, user):
        tree = Tree(cls.root_name)
        for folder in cls.folder_model.objects.all():
            tree._add(folder)

        if user is not None:
            cls._limit_visible_tree_part(tree, user)

        _sort_levels(tree.root)
        return tree

    @classmethod
    def _limit_visible_tree_part(cls, tree, user):
        if user.is_staff:
            _enforce_acl(tree.root, {}, AccessMode.WRITE)
        else:
            acl = {}
            for folder_id, in cls.get_extra_folders(user).values_list('id').order_by():
                acl[folder_id] = 0

            if user.is_authenticated and getattr(user, 'is_admin', True):
                for folder_id, mode in filter_admingroups(cls.folder_access_model.objects, user).values_list('folder_id', 'mode'):
                    acl[folder_id] = mode

            _enforce_acl(tree.root, acl, 0)  # root is always shown

        tree._reindex()

    @classmethod
    def load_node(cls, user, folder_id):
        # faster?
        return cls.load_tree(user).get(folder_id)

    @classmethod
    def get_folder_content(cls, user, node):
        raise NotImplementedError()

    @classmethod
    def get_extra_object_pks(cls, user):
        return []

    @classmethod
    def get_extra_folders(cls, user):
        return cls.folder_model.objects.none()
