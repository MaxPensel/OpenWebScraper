"""
Created on 13.09.2019

@author: Maximilian Pensel
"""
import json
import core

LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)


class CrawlSpecification:

    def __init__(self,
                 name: str = None,
                 workspace: str = None,
                 urls: [str] = None,
                 blacklist: [str] = None,
                 parser: str = None,
                 parser_data: {} = None,
                 pipelines: {} = None,
                 finalizers: {} = None):

        self.name = name
        self.workspace = workspace

        if urls is None:
            urls = list()
        self.urls = urls

        if blacklist is None:
            blacklist = list()
        self.blacklist = blacklist

        self.parser = parser

        if parser_data is None:
            parser_data = dict()
        self.parser_data = parser_data

        if pipelines is None:
            pipelines = dict()
        self.pipelines = pipelines

        if finalizers is None:
            finalizers = dict()
        self.finalizers = finalizers

    def update(self,
               name: str = None,
               workspace: str = None,
               urls: [str] = None,
               blacklist: [str] = None,
               parser: str = None,
               parser_data: {} = None,
               pipelines: {} = None,
               finalizers: {} = None):
        if name:
            self.name = name
        if workspace:
            self.workspace = workspace
        if urls:
            self.urls = urls
        if blacklist:
            self.blacklist = blacklist
        if parser:
            self.parser = parser
        if parser_data:
            self.parser_data = parser_data
        if pipelines:
            self.pipelines = pipelines
        if finalizers:
            self.finalizers = finalizers

    def serialize(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))

    def deserialize(self, json_str):
        data = json.loads(json_str)
        for key in data:
            setattr(self, key, data[key])
