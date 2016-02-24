from django import forms


from constants import EMPTY_SELECT, TREE_LEVEL_INDICATOR


class OrderedTreeNodeChoiceFieldMixin(object):
    class _Node(object):
        def __init__(self, object_id, label):
            self.object_id = object_id
            self.label = label
            self.children = []

    def _dfs(self, nodes, level, out):
        nodes.sort(key=lambda n: n.label)
        for node in nodes:
            out.append((node.object_id, (TREE_LEVEL_INDICATOR * level) + ' ' + node.label))
            self._dfs(node.children, level + 1, out)

    def _make_sorted_choices(self):
        nodes = {}
        roots = []
        queryset = self.queryset

        for obj in queryset:
            nodes[obj.pk] = OrderedTreeNodeChoiceField._Node(obj.pk, self.label_from_instance(obj))

        for obj in queryset:
            node = nodes[obj.pk]
            if obj.parent_id is None:
                roots.append(node)
            else:
                nodes[obj.parent_id].children.append(node)

        self._choices = []
        if self.empty_label is not None:
            self._choices.append(('', EMPTY_SELECT))
        self._dfs(roots, 0, self._choices)


class OrderedTreeNodeChoiceField(OrderedTreeNodeChoiceFieldMixin, forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        super(OrderedTreeNodeChoiceField, self).__init__(*args, **kwargs)
        self._make_sorted_choices()


class OrderedTreeNodeMultipleChoiceField(OrderedTreeNodeChoiceFieldMixin, forms.ModelMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        super(OrderedTreeNodeMultipleChoiceField, self).__init__(*args, **kwargs)
        self._make_sorted_choices()
