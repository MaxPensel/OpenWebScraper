"""
Created on 13.09.2019

@author: Maximilian Pensel
"""
import json
import core

LOG = core.simple_logger(modname="crawler", file_path=core.MASTER_LOG)

class CrawlMode():
    # ignore any previous content under that crawl name and start a new crawl
    NEW = "new"

    # only works on specifications contained in running/ dir
    CONTINUE = "continue"

    # only works on specifications that have been moved to data/ dir, attempts to recrawl only urls for which no
    # paragraphs have been stored in the workspace
    RECRAWL_EMPTY = "recrawl"


class CrawlSpecification:

    def __init__(self,
                 name: str = None,
                 workspace: str = None,
                 urls: [str] = [],
                 blacklist: [str] = [],
                 xpaths: [str] = [],
                 pipelines: {} = {},
                 mode: str = CrawlMode.NEW):
        self.name = name
        self.workspace = workspace
        self.urls = urls
        self.blacklist = blacklist
        self.xpaths = xpaths
        self.mode = mode
        self.pipelines = pipelines

    def update(self,
               name: str = None,
               workspace: str = None,
               urls: [str] = [],
               blacklist: [str] = [],
               xpaths: [str] = [],
               pipelines: {} = [],
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
        if isinstance(mode, str) and mode in CrawlMode.__dict__.values():  # only update valid modes
            self.mode = mode
        else:
            if mode:
                LOG.error("'{0}' is not a valid CrawlMode.".format(mode))

    def serialize(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))

    def deserialize(self, json_str):
        data = json.loads(json_str)
        for key in data:
            setattr(self, key, data[key])
