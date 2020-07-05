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
        return str(self._custom_name)

    @property
    def id(self):
        return None


class Tree(object):
    def __init__(self, root_name):
        self.root = RootNode(root_name)
        self._key2node = {None: self.root}

    def find(self, key):
        return self._key2node[key]

    def get(self, key):
        return self._key2node.get(key)

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

    def _reindex(self):
        self._key2node = {k: v for k, v in self._key2node.items() if v.access >= 0}

    def as_choices(self, show_root=True):
        choices = []

        def _dfs(node, level):
            choices.append((node.id, ('— ' * level) + node.name))
            for child in node.children:
                _dfs(child, level + 1)

        if show_root:
            _dfs(self.root, 0)
        else:
            for child in self.root.children:
                _dfs(child, 0)

        return choices
