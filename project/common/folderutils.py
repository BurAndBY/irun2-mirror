from __future__ import unicode_literals

import json

from django.utils.encoding import force_text

from common.tree.key import FolderId


def _fancytree_recursive_node_to_dict(node):
    result = {
        'key': FolderId.to_string(node.id),
        'title': force_text(node.name),
        'folder': True,
    }
    children = [_fancytree_recursive_node_to_dict(c) for c in node.children]
    if children:
        result['children'] = children
    return result


def make_fancytree_json(tree):
    result = _fancytree_recursive_node_to_dict(tree.root)
    return json.dumps([result])
