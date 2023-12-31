import uuid
from collections import namedtuple

from django import template
from django.urls import reverse

from common.folderutils import make_fancytree_json
from common.tree.key import FolderId
from common.tree.inmemory import Tree

register = template.Library()

'''
Helper types
'''
BreadcrumbItem = namedtuple('BreadcrumbItem', 'folder_id folder_id_or_root name is_link')
SubfolderItem = namedtuple('SubfolderItem', 'folder_id name')
TemplateTreeItem = namedtuple('TemplateTreeItem', 'kind breadcrumb')


def _name_extractor(f):
    return f.name


def ensure_trees(value):
    if not isinstance(value, Tree):
        raise TypeError('Type {} expected, {} found'.format(Tree.__name__, type(value).__name__))


def _make_breadcrumb(node, link):
    return BreadcrumbItem(node.id, FolderId.to_string(node.id), node.name, link)


__marker = object()


@register.inclusion_tag('common/irunner_folders_tree_tag.html')
def irunner_folders_tree(tree, url_pattern=None, folder_id=__marker, mode='irunner_dynamic'):
    '''
    args:
        tree:
            inmemory.Tree instance
        url_pattern:
            pattern to use to resolve links to folders, must have single parameter
        folder_id:
            current folder id (integer, 'root', None)
        mode:
            display mode to use
    '''
    ensure_trees(tree)

    if mode == 'fancy':
        context = _fill_fancytree_data(tree)
    elif mode == 'irunner':
        context = _fill_irunnertree_data(tree, folder_id, dynamic=False)
    elif mode == 'irunner_dynamic':
        context = _fill_irunnertree_data(tree, folder_id, dynamic=True)
    else:
        raise ValueError('unsupported mode')

    context['folder_id_or_root'] = FolderId.to_string(folder_id)
    context['url_pattern'] = url_pattern
    return context


@register.inclusion_tag('common/irunner_folders_breadcrumbs_tag.html')
def irunner_folders_breadcrumbs(tree, url_pattern, folder_id, last_link=False):
    '''
    args: the same as above
    '''
    ensure_trees(tree)

    breadcrumbs = []
    current = tree.find(folder_id)
    for node in tree.get_ancestors(current):
        breadcrumbs.append(_make_breadcrumb(node, True))
    breadcrumbs.append(_make_breadcrumb(current, last_link))

    return {
        'breadcrumbs': breadcrumbs,
        'url_pattern': url_pattern
    }


@register.inclusion_tag('common/irunner_folders_subfolders_tag.html')
def irunner_folders_subfolders(tree, url_pattern, folder_id):
    '''
    args: the same as above
    '''
    ensure_trees(tree)

    subfolders = []
    current = tree.find(folder_id)
    for node in current.children:
        subfolders.append(SubfolderItem(node.id, node.name))
    subfolders.sort(key=_name_extractor)

    return {
        'subfolders': subfolders,
        'url_pattern': url_pattern
    }


@register.simple_tag
def irunner_folders_url(url_pattern, folder_id):
    return reverse(url_pattern, args=(FolderId.to_string(folder_id),))


'''
Implementation details follow...
'''


def _fill_fancytree_data(tree):
    return {
        'ft_data': make_fancytree_json(tree),
        'uid': uuid.uuid1().hex
    }


def _fill_irunnertree_data(tree, folder_id, dynamic):
    output = []
    _irunnertree_traverse(tree.root, folder_id, dynamic, output)
    return {
        'it_data': output,
        'uid': uuid.uuid1().hex,
        'dynamic': dynamic,
    }


def _irunnertree_traverse(node, target_id, dynamic, output):
    children = node.children

    target = None
    temp_output = []
    for child in sorted(children, key=_name_extractor):
        result = _irunnertree_traverse(child, target_id, dynamic, temp_output)
        if result is not None:
            target = result

    if node.id == target_id:
        target = node
        if children:
            output.append(TemplateTreeItem('-', _make_breadcrumb(node, False)))
            output.append(TemplateTreeItem('(', None))
            output.extend(temp_output)
            output.append(TemplateTreeItem(')', None))
        else:
            output.append(TemplateTreeItem('.', _make_breadcrumb(node, False)))
    else:
        if target is not None:
            output.append(TemplateTreeItem('-', _make_breadcrumb(node, True)))
            output.append(TemplateTreeItem('(', None))
            output.extend(temp_output)
            output.append(TemplateTreeItem(')', None))
        else:
            if children:
                output.append(TemplateTreeItem('+', _make_breadcrumb(node, True)))
            else:
                output.append(TemplateTreeItem('.', _make_breadcrumb(node, True)))
            if dynamic:
                output.append(TemplateTreeItem('(*', None))
                output.extend(temp_output)
                output.append(TemplateTreeItem(')', None))
    return target
