"""
Created on 13.09.2019

@author: Maximilian Pensel

Copyright 2019 Maximilian Pensel <maximilian.pensel@gmx.de>

This file is part of OpenWebScraper.

OpenWebScraper is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenWebScraper is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenWebScraper.  If not, see <https://www.gnu.org/licenses/>.
"""
import json
import core
from crawlUI import APP_SETTINGS

LOG = core.simple_logger(modname="crawler", file_path=APP_SETTINGS["general"]["master_log"])


class CrawlSpecification:

    def __init__(self,
                 name: str = None,
                 output: str = None,
                 logs: str = None,
                 urls: [str] = None,
                 blacklist: [str] = None,
                 parser: str = None,
                 parser_data: {} = None,
                 pipelines: {} = None,
                 finalizers: {} = None):

        self.name = name
        self.output = output
        self.logs = logs

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
               output: str = None,
               logs: str = None,
               urls: [str] = None,
               blacklist: [str] = None,
               parser: str = None,
               parser_data: {} = None,
               pipelines: {} = None,
               finalizers: {} = None):
        if name:
            self.name = name
        if output:
            self.output = output
        if logs:
            self.logs = logs
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

    def serialize(self, pretty=True):
        if pretty:
            return json.dumps(self.__dict__, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.__dict__, sort_keys=True, separators=(',', ':'))

    def deserialize(self, json_str):
        data = json.loads(json_str)
        for key in data:
            setattr(self, key, data[key])
