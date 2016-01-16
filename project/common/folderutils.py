import json
from collections import namedtuple

from django.http import Http404

ROOT = 'root'

# id may be integer (then object is not None) or ROOT (the object is None)
NodeEx = namedtuple('NodeEx', 'object folder_id')


def cast_id(folder_id):
    '''
    cast is idempotent:
    cast_id(cast_id(x)) = cast_id(x)
    '''
    if folder_id is None:
        return None
    if folder_id == ROOT:
        return None
    return int(folder_id)


def ensure_trees(cached_trees):
    if not isinstance(cached_trees, list):
        raise ValueError('cached_trees must be a list returned by get_cached_trees() from MPTT module')


def lookup_node_ex(folder_id_or_root, cached_trees):
    folder_id = cast_id(folder_id_or_root)
    if folder_id is None:
        return NodeEx(None, None)
    else:
        obj = find_in_tree(cached_trees, folder_id)
        if obj is None:
            raise Http404('folder {0} does not exist'.format(folder_id))
        return NodeEx(obj, folder_id)


def find_in_tree(cached_trees, target_id):
    for node in cached_trees:
        if node.id == target_id:
            return node
        children = node.get_children()
        if children:
            result = find_in_tree(children, target_id)
            if result is not None:
                return result
    return None


def _fancytree_recursive_node_to_dict(node):
    result = {
        'key': node.pk,
        'title': node.name,
        'folder': True,
    }
    children = [_fancytree_recursive_node_to_dict(c) for c in node.get_children()]
    if children:
        result['children'] = children
    return result


def make_fancytree_json(cached_trees, root_name):
    dicts = []
    for node in cached_trees:
        dicts.append(_fancytree_recursive_node_to_dict(node))

    result = {
        'key': ROOT,
        'title': unicode(root_name),
        'folder': True,
        'children': dicts
    }
    return json.dumps([result])
