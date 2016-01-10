import uuid
from collections import namedtuple

from django import template

from common.folderutils import ROOT, ensure_trees, cast_id, make_fancytree_json, find_in_tree

register = template.Library()

'''
Helper types
'''
BreadcrumbItem = namedtuple('BreadcrumbItem', 'folder_id_or_root name is_link')
SubfolderItem = namedtuple('SubfolderItem', 'folder_id_or_root name')
TemplateTreeItem = namedtuple('TemplateTreeItem', 'kind breadcrumb')

def _name_extractor(f):
    return f.name

@register.inclusion_tag('common/irunner_folders_tree_tag.html')
def irunner_folders_tree(cached_trees, url_pattern, folder_id, root_name, mode='irunner'):
    '''
    args:
        cached_trees:
            list of roots returned by mptt.get_cached_trees()
        url_pattern:
            pattern to use to resolve links to folders, must have single parameter
        folder_id:
            current folder id (integer, 'root', None)
        root_name:
            human-readable name of the root node
        mode:
            display mode to use
    '''
    ensure_trees(cached_trees)
    folder_id = cast_id(folder_id)

    if mode == 'fancy':
        context = _fill_fancytree_data(cached_trees, root_name)
    elif mode == 'irunner':
        context = _fill_irunnertree_data(cached_trees, folder_id, root_name)
    else:
        raise ValueError('unsupported mode')

    context['folder_id_or_root'] = folder_id if folder_id is not None else ROOT
    context['url_pattern'] = url_pattern
    return context


@register.inclusion_tag('common/irunner_folders_breadcrumbs_tag.html')
def irunner_folders_breadcrumbs(cached_trees, url_pattern, folder_id, root_name):
    '''
    args: the same as above
    '''
    ensure_trees(cached_trees)
    folder_id = cast_id(folder_id)

    breadcrumbs = []
    if folder_id is None:
        breadcrumbs.append(BreadcrumbItem(ROOT, root_name, False))
    else:
        current = find_in_tree(cached_trees, folder_id)

        breadcrumbs.append(BreadcrumbItem(ROOT, root_name, True))
        for node in current.get_ancestors():
            breadcrumbs.append(BreadcrumbItem(node.id, node.name, True))
        breadcrumbs.append(BreadcrumbItem(current.id, current.name, False))

    return {
        'breadcrumbs': breadcrumbs,
        'url_pattern': url_pattern
    }


@register.inclusion_tag('common/irunner_folders_subfolders_tag.html')
def irunner_folders_subfolders(cached_trees, url_pattern, folder_id):
    '''
    args: the same as above
    '''
    ensure_trees(cached_trees)
    folder_id = cast_id(folder_id)

    subfolders = []

    if folder_id is None:
        for node in cached_trees:
            subfolders.append(SubfolderItem(node.id, node.name))
    else:
        current = find_in_tree(cached_trees, folder_id)

        for node in current.get_children():
            subfolders.append(SubfolderItem(node.id, node.name))

    subfolders.sort(key=_name_extractor)

    return {
        'subfolders': subfolders,
        'url_pattern': url_pattern
    }


@register.inclusion_tag('common/irunner_folders_url_tag.html')
def irunner_folders_url(url_pattern, folder_id):
    return {
        'url_pattern': url_pattern,
        'folder_id': folder_id if folder_id is not None else ROOT
    }


'''
Implementation details follow...
'''


def _fill_fancytree_data(cached_trees, root_name):
    return {
        'ft_data': make_fancytree_json(cached_trees, root_name),
        'uid': uuid.uuid1().hex
    }


def _fill_irunnertree_data(cached_trees, folder_id, root_name):
    output = []

    output.append(TemplateTreeItem('-', BreadcrumbItem(ROOT, root_name, folder_id is not None)))
    for root in sorted(cached_trees, key=_name_extractor):
        output.append(TemplateTreeItem('(', None))
        _irunnertree_traverse(root, folder_id, output)
        output.append(TemplateTreeItem(')', None))

    return {
        'it_data': output
    }


def _irunnertree_traverse(node, target_id, output):
    children = node.get_children()

    target = None
    temp_output = []
    for child in sorted(children, key=_name_extractor):
        result = _irunnertree_traverse(child, target_id, temp_output)
        if result is not None:
            target = result

    if node.id == target_id:
        target = node
        if children:
            output.append(TemplateTreeItem('-', BreadcrumbItem(node.id, node.name, False)))
            output.append(TemplateTreeItem('(', None))
            output.extend(temp_output)
            output.append(TemplateTreeItem(')', None))
        else:
            output.append(TemplateTreeItem('.', BreadcrumbItem(node.id, node.name, False)))
    else:
        if target is not None:
            output.append(TemplateTreeItem('-', BreadcrumbItem(node.id, node.name, True)))
            output.append(TemplateTreeItem('(', None))
            output.extend(temp_output)
            output.append(TemplateTreeItem(')', None))
        else:
            if children:
                output.append(TemplateTreeItem('+', BreadcrumbItem(node.id, node.name, True)))
            else:
                output.append(TemplateTreeItem('.', BreadcrumbItem(node.id, node.name, True)))
    return target
