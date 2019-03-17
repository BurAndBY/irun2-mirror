import os
import tempfile
import pathlib


class Cache:
    EMPTY_FILE_NAME = '_empty'

    def __init__(self, root):
        self._root = pathlib.Path(root)
        if not self._root.is_dir():
            self._root.mkdir()

    def get(self, resource_id):
        target_path = self._path(resource_id)
        if not target_path.is_file():
            return None
        return target_path

    def put(self, resource_id, blob):
        target_path = self._path(resource_id)
        if not target_path.is_file():
            with tempfile.NamedTemporaryFile(prefix='_', dir=self._root, delete=False) as fd:
                fd.write(blob)
                temp_path = fd.name
            os.chmod(temp_path, 0o444)
            os.rename(temp_path, target_path)
        return target_path

    def __getitem__(self, resource_id):
        result = self.get(resource_id)
        if result is None:
            raise KeyError('Resource "{}" is not found'.format(resource_id.hexstr))
        return result

    def __contains__(self, resource_id):
        return self.get(resource_id) is not None

    def _path(self, resource_id):
        name = resource_id.hexstr
        if len(name) == 0:
            name = self.EMPTY_FILE_NAME
        return self._root / name
