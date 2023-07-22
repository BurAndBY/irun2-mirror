# -*- coding: utf-8 -*-

from wsgiref.util import FileWrapper

from .resource_id import ResourceId
from .storage_base import DataStorage, ServedData

from gridfs import GridFSBucket
from gridfs.errors import NoFile
from pymongo import MongoClient


class GridFsStorage(DataStorage):
    def __init__(self, uri):
        self._db = MongoClient(uri).filestorage
        self._fs = GridFSBucket(self._db)

    def _do_save(self, resource_id, f):
        print('_do_save')
        with self._fs.open_upload_stream(str(resource_id)) as grid_in:
            for chunk in f.chunks():
                grid_in.write(chunk)

    def _do_get_size_on_disk(self, resource_id):
        print('_get_size_on_disk')
        try:
            with self._fs.open_download_stream_by_name(str(resource_id)) as grid_out:
                return grid_out.length
        except NoFile:
            return 0

    def _do_serve(self, resource_id):
        print('_do_serve')
        try:
            grid_out = self._fs.open_download_stream_by_name(str(resource_id))
            return ServedData(grid_out.length, FileWrapper(grid_out))
        except NoFile:
            return None

    def _do_read_with_size(self, resource_id, max_size):
        print('_do_read_with_size')
        try:
            with self._fs.open_download_stream_by_name(str(resource_id)) as grid_out:
                blob = grid_out.read() if max_size is None else grid_out.read(max_size)
                return (blob, grid_out.length)
        except NoFile:
            return (None, 0)

    def _do_get_existing_files(self, resource_ids):
        print('_do_get_existing_files')
        names = [str(resource_id) for resource_id in resource_ids]
        res = set()
        for fd in self._fs.find({"filename": {"$in": names}}):
            res.add(ResourceId.parse(fd.filename))
        return res

    def list_all(self):
        for entry in self._fs.find():
            yield (entry.filename, entry.length)
