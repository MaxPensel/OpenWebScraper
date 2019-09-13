"""
Created on 13.09.2019

@author: Maximilian Pensel
"""
import json


class CrawlSpecification:

    def __init__(self,
                 name: str = None,
                 workspace: str = None,
                 urls: [str] = [],
                 blacklist: [str] = [],
                 xpaths: [str] = []):
        self.name = name
        self.workspace = workspace
        self.urls = urls
        self.blacklist = blacklist
        self.xpaths = xpaths

    def update(self,
               name: str = None,
               workspace: str = None,
               urls: [str] = [],
               blacklist: [str] = [],
               xpaths: [str] = []):
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

    def serialize(self):
        return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))

    def deserialize(self, json_str):
        self.__dict__ = json.loads(json_str)
