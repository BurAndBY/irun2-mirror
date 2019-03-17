def download(api_client, cache, resource_ids):
    '''
    Returns a dict: resource_id -> path
    '''
    result = {}
    for resource_id in resource_ids:
        path = cache.path(resource_id)
        if path is None:
            blob = api_client.fs_download_data(resource_id)
            path = cache.put(resource_id, blob)
        result[resource_id] = path

    return result
