from cauth.acl.accessmode import AccessMode


class Node(object):
    __slots__ = ('instance', 'children', 'access')

    def __init__(self, instance):
        self.instance = instance
        self.children = []
        self.access = None

    @property
    def name(self):
        return self.instance.name

    @property
    def id(self):
        return self.instance.id


class RootNode(Node):
    __slots__ = ('_custom_name')

    def __init__(self, name):
        super().__init__(None)
        self._custom_name = name

    @property
    def name(self):
        return self._custom_name

    @property
    def id(self):
        return None


def _enforce_acl(node, acl, mode):
    mode = max(mode, acl.get(node.id, 0))
    node.access = mode
    children_left = []
    for child in node.children:
        if _enforce_acl(child, acl, mode):
            children_left.append(child)
    node.children = children_left
    return (mode > 0) or node.children


class Tree(object):
    def __init__(self, root_name):
        self.root = RootNode(root_name)
        self._key2node = {None: self.root}

    @staticmethod
    def load(root_name, cls, access_cls, user):
        tree = Tree(root_name)

        for folder in cls.objects.all():
            tree._add(folder)

        acl = {}
        if access_cls is not None:
            if user.is_authenticated:
                for folder_id, mode in access_cls.objects.filter(group__users=user).values_list('folder_id', 'mode'):
                    acl[folder_id] = mode

        mode = AccessMode.WRITE if user.is_staff else 0
        _enforce_acl(tree.root, acl, mode)
        return tree

    def find(self, key):
        return self._key2node[key]

    def get_ancestors(self, node):
        res = []
        while node.instance is not None:
            parent = self._key2node[node.instance.parent_id]
            res.append(parent)
            node = parent
        res.reverse()
        return res

    def _add(self, folder):
        node = Node(folder)
        self._key2node[folder.id] = node
        self._key2node[folder.parent_id].children.append(node)
