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
                 xpaths: [str] = None,
                 pipelines: {} = None):

        self.name = name
        self.workspace = workspace

        if urls is None:
            urls = list()
        self.urls = urls

        if blacklist is None:
            blacklist = list()
        self.blacklist = blacklist

        if xpaths is None:
            xpaths = list()
        self.xpaths = xpaths

        # if pipelines is None:
        #     pipelines = dict()
        # self.pipelines = pipelines
        # fixing this for now:
        self.pipelines = {"modules.crawler.scrapy.pipelines.Paragraph2WorkspacePipeline": 300}

    def update(self,
               name: str = None,
               workspace: str = None,
               urls: [str] = None,
               blacklist: [str] = None,
               xpaths: [str] = None,
               pipelines: {} = None,
               mode: str = None):
        if name:
            self.name = name
        if workspace:
            self.workspace = workspace
        if urls:
            self.urls = urls
        if blacklist:
            self.blacklist = blacklist
        if xpaths:
            self.xpaths = xpaths
        if pipelines:
            self.pipelines = pipelines

    def serialize(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))

    def deserialize(self, json_str):
        data = json.loads(json_str)
        for key in data:
            setattr(self, key, data[key])
