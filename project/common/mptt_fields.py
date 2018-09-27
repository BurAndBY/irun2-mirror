from django import forms


from common.constants import EMPTY_SELECT, TREE_LEVEL_INDICATOR


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

    def _make_sorted_choices(self, queryset):
        nodes = {}
        roots = []

        object_list = list(queryset.iterator())

        for obj in object_list:
            nodes[obj.pk] = OrderedTreeNodeChoiceField._Node(obj.pk, self.label_from_instance(obj))

        for obj in object_list:
            node = nodes[obj.pk]
            if obj.parent_id is None:
                roots.append(node)
            else:
                nodes[obj.parent_id].children.append(node)

        choices_list = []
        if self.empty_label is not None:
            choices_list.append(('', EMPTY_SELECT))
        self._dfs(roots, 0, choices_list)
        return choices_list

    def _set_queryset(self, queryset):
        if queryset is not None:
            self._choices = self._make_sorted_choices(queryset)
        super(OrderedTreeNodeChoiceFieldMixin, self)._set_queryset(queryset)

    def _get_queryset(self):
        return super(OrderedTreeNodeChoiceFieldMixin, self)._get_queryset()

    queryset = property(_get_queryset, _set_queryset)


class OrderedTreeNodeChoiceField(OrderedTreeNodeChoiceFieldMixin, forms.ModelChoiceField):
    pass


class OrderedTreeNodeMultipleChoiceField(OrderedTreeNodeChoiceFieldMixin, forms.ModelMultipleChoiceField):
    pass
